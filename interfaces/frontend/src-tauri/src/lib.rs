use tauri_plugin_shell::ShellExt;

mod tray;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("안녕하세요, {}님! 세컨드 브레인입니다.", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Python 백엔드 sidecar 실행
            let shell = app.shell();

            let sidecar_command = shell.sidecar("binaries/python-backend")
                .expect("python-backend sidecar를 찾을 수 없습니다");

            let (mut rx, _child) = sidecar_command
                .spawn()
                .expect("python-backend 실행에 실패했습니다");

            // 백엔드 출력 로깅
            tauri::async_runtime::spawn(async move {
                use tauri_plugin_shell::process::CommandEvent;
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            let line_str = String::from_utf8_lossy(&line);
                            println!("[Backend] {}", line_str);
                        }
                        CommandEvent::Stderr(line) => {
                            let line_str = String::from_utf8_lossy(&line);
                            eprintln!("[Backend Error] {}", line_str);
                        }
                        CommandEvent::Terminated(payload) => {
                            println!("[Backend] 종료됨: {:?}", payload);
                        }
                        _ => {}
                    }
                }
            });

            // 시스템 트레이 설정
            tray::create_tray(app)?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("세컨드 브레인 실행 중 오류가 발생했습니다");
}
