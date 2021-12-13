use std::env;
use std::io::Write;
use std::path::Path;
use std::process::{Command, Stdio};

fn main() {
    let out_dir = env::var("OUT_DIR").unwrap();
    // FIXME: maybe pyo3-build-config should provide a way to do this?
    let python = env::var("PYO3_PYTHON").unwrap_or_else(|_| "python3".to_string());
    println!("cargo:rerun-if-changed=../_cffi_src/");
    let python_path = match env::var("PYTHONPATH") {
        Ok(mut val) => {
            val.push_str(":../");
            val
        }
        Err(_) => "../".to_string(),
    };
    let output = Command::new(&python)
        .env("PYTHONPATH", python_path)
        .env("OUT_DIR", &out_dir)
        .arg("../_cffi_src/build_openssl.py")
        .output()
        .expect("failed to execute build_openssl.py");
    if !output.status.success() {
        panic!(
            "failed to run build_openssl.py, stdout: \n{}\nstderr: \n{}\n",
            String::from_utf8(output.stdout).unwrap(),
            String::from_utf8(output.stderr).unwrap()
        );
    }

    let stdout = String::from_utf8(output.stdout).unwrap();
    for line in stdout.lines() {
        if line.starts_with("cargo:") {
            println!("{}", line);
        }
    }
    let python_include = run_python_script(
        &python,
        "import sysconfig; print(sysconfig.get_path('include'), end='')",
    )
    .unwrap();
    let openssl_include =
        std::env::var_os("DEP_OPENSSL_INCLUDE").expect("unable to find openssl include path");
    let openssl_c = Path::new(&out_dir).join("_openssl.c");
    cc::Build::new()
        .file(openssl_c)
        .include(python_include)
        .include(openssl_include)
        .compile("_openssl.a");
}

/// Run a python script using the specified interpreter binary.
fn run_python_script(interpreter: impl AsRef<Path>, script: &str) -> Result<String, String> {
    let interpreter = interpreter.as_ref();
    let out = Command::new(interpreter)
        .env("PYTHONIOENCODING", "utf-8")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
        .and_then(|mut child| {
            child
                .stdin
                .as_mut()
                .expect("piped stdin")
                .write_all(script.as_bytes())?;
            child.wait_with_output()
        });

    match out {
        Err(err) => Err(format!(
            "failed to run the Python interpreter at {}: {}",
            interpreter.display(),
            err
        )),
        Ok(ok) if !ok.status.success() => Err(format!(
            "Python script failed: {}",
            String::from_utf8(ok.stderr).expect("failed to parse Python script output as utf-8")
        )),
        Ok(ok) => Ok(
            String::from_utf8(ok.stdout).expect("failed to parse Python script output as utf-8")
        ),
    }
}
