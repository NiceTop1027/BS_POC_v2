# BloodStrike CTF ESP - 안정형 Aim V3

## 목적

검증 중 보고된 "aim FOV 원 밖인데도 우클릭 조준 시 화면이 흔들림" 문제를 막기 위한 별도 안정형 빌드다. 기존 V1/V2 배포본은 보존하고, 이 폴더는 원 밖 입력 차단 검증용으로 사용한다.

## 핵심 수정

- locked target도 aim FOV 원 밖이면 즉시 후보에서 제외
- locked target이 원 밖/비정상 상태가 되면 락을 즉시 해제
- `SendInput` 호출 직전 최종 조준점이 aim FOV 밖이면 입력을 차단
- 후보 선택 기준을 최종 head/aim point 기준으로 재검사
- `prediction=0`으로 예측 보정 비활성화
- 낮은 gain, 큰 deadzone, 약 30Hz 입력 제한 유지
- PC별 감도 자동 학습은 유지하되 synthetic `SendInput` 샘플은 학습에 사용하지 않음

## 실행

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\run_poc.ps1
```

관리자 권한 승인이 뜨면 승인한다. `BloodStrike.exe` CTF 인스턴스가 먼저 실행 중이어야 한다.

## 검증 기준

- 우클릭을 누르고 있어도 적 head/aim point가 원 밖이면 화면이 움직이면 안 된다.
- 원 안에 들어온 뒤에만 천천히 보정되어야 한다.
- 타겟이 원 밖으로 나가면 조준 락이 끊기고 입력이 멈춰야 한다.

## 포함 파일

- `BloodStrikeCTFESP.exe`: 안정형 V3 C++ 오버레이
- `ctf_overlay_settings.ini`: 오버레이 설정
- `ctf_native_esp_config.txt`: native snapshot/exporter 설정
- `ctf_native_snapshot_code.py`: CTF 인스턴스 state exporter
- `remote_py_run.py`: 인스턴스 내 exporter 실행 helper
- `run_poc.ps1`: 관리자 권한 실행 스크립트
