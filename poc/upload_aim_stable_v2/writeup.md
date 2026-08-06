# BloodStrike CTF ESP - 안정형 Aim V2

## 목적

검증자 PC마다 마우스 감도, FOV, 창 크기, 프레임 타이밍이 달라 조준 보정이 흔들리는 문제를 줄인 별도 안정형 빌드다. 기존 `upload_fps_esp_maker` 배포본은 그대로 두고, 이 폴더는 흔들림 완화 검증용으로만 사용한다.

## 변경점

- `prediction=0` 기본값으로 이동/탄도 예측 보정을 끔
- 조준 보정 gain을 낮추고 입력 주기를 약 30Hz로 제한
- 조준 중심부 deadzone을 키워 ±1~2 raw mouse 왕복 입력 제거
- 스코프 상태에서 horizontal/vertical 보정을 더 약하게 적용
- 실행 중 PC별 raw mouse 입력과 카메라 변화로 감도를 자동 학습하되, 충분한 샘플이 쌓이기 전까지는 안전한 기본값 사용
- 자기 자신이 보낸 `SendInput` 기반 synthetic 보정 샘플은 안정형에서 사용하지 않음

## 실행

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\run_poc.ps1
```

관리자 권한 승인이 뜨면 승인한다. `BloodStrike.exe` 인스턴스가 실행 중이어야 한다.

## 포함 파일

- `BloodStrikeCTFESP.exe`: 안정형 V2 C++ 오버레이
- `ctf_overlay_settings.ini`: 오버레이 설정
- `ctf_native_esp_config.txt`: native snapshot/exporter 설정
- `ctf_native_snapshot_code.py`: CTF 인스턴스 state exporter
- `remote_py_run.py`: 인스턴스 내 exporter 실행 helper
- `run_poc.ps1`: 관리자 권한 실행 스크립트

## 검증 포인트

우클릭 조준 시 타겟으로 붙는 속도는 이전 빌드보다 느릴 수 있다. 대신 검증자 PC에서 화면이 좌우/상하로 왕복 흔들리는 현상을 줄이는 것이 이 빌드의 목표다.
