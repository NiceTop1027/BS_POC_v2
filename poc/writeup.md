# BloodStrike CTF - 실제 엔티티 기반 ESP

## 대상

- 바이너리: `C:\Program Files (x86)\bloodstrike\Engine\Binaries\Win64\BloodStrike.exe`
- SHA-256: `62AF2CDD3ABECB6A77A848ACD58F3E1F680950926B164B6C42EDEF9BF791E908`
- 현재 인스턴스 PID: `9316`
- 범위: 주최자가 제공한 격리 CTF 인스턴스

## 핵심 관찰

이전 C++ 오버레이는 고정 좌표 박스를 메모리 값으로 게이트한 형태라 실제 ESP 증거로 보지 않고 폐기했다.

실제 성공 경로는 `BloodStrike.exe`에 포함된 CPython 런타임을 이용해 게임 프로세스 안에서 Python 코드를 실행한 뒤, 게임 내부 엔티티 매니저와 UI API를 직접 호출하는 방식이다.

- `PyRun_SimpleStringFlags` live address: `0x7ff747751900`
- `common.EntityManager.EntityManager._entities`: 현재 엔티티 딕셔너리
- 플레이어 combat avatar: `PlayerCombatAvatarShootingRange`
- 로봇 combat avatar: `RobotCombatAvatarShootingRange`
- 로봇 UI 경로: `EnsureShootingRangeToplogo`, `ShowEnemyToplogo`, `SetToplogoVisible`, `AddToplogoVisibleTick`, `EnemyTopLogoTimer`, `RefreshToplogo`
- 추가 마커 경로: `CreateCommonMarkToplogoSceneOnly`, `CreateMarkWorldEffect`

## 구현

- `remote_py_run.py`: BloodStrike 프로세스 안에서 짧은 Python 코드를 실행하는 런너
- `ctf_live_esp_code.py`: 실제 ESP 설치 코드
- `ctf_live_esp.log`: 엔티티 좌표, UI 호출 성공 여부, 타이머 설치 증거
- `bloodstrike-live-esp-game.png`: 게임 창에서 확인한 시각 증거

설치 코드는 `PlayerCombatAvatarShootingRange.add_repeat_timer(delay, func)`에 반복 타이머를 붙인다. 매 tick마다 `EntityManager._entities`를 읽고 로봇을 골라 게임 내부 toplogo와 common mark를 갱신한다.

## 검증 결과

설치 로그에서 로봇 6개와 플레이어 1개가 실제 엔티티로 확인됐다.

```text
INSTALL_OK owner=<PlayerCombatAvatarShootingRange(anFFZUsxNr+4vT0l)> timer_id=-691
```

각 로봇에 대해 다음 호출이 성공했다.

```text
ready_after=True
CreateCommonMarkToplogoSceneOnly=ok
CreateMarkWorldEffect=ok
```

시각 검증 이미지:

```text
C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\bloodstrike-live-esp-game.png
```

## 재현

BloodStrike 인스턴스가 실행 중인 상태에서:

```powershell
cd C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc
$PidValue=(Get-Process -Name BloodStrike -ErrorAction Stop | Select-Object -First 1 -ExpandProperty Id)
$Python=(Get-Command python.exe -ErrorAction Stop).Source
$Script=(Resolve-Path .\remote_py_run.py).Path
$Code=(Resolve-Path .\ctf_live_esp_code.py).Path
$Out=(Join-Path (Resolve-Path .).Path 'remote-py-run-live-esp-reinstall.json')
Start-Process -Verb RunAs -FilePath $Python -WorkingDirectory (Resolve-Path .).Path -ArgumentList @($Script,'--pid',([string]$PidValue),'--code-file',$Code,'--out',$Out) -Wait
Get-Content .\ctf_live_esp.log -Tail 50
```

## 플래그

아직 플래그 문자열은 도구 출력에서 확인되지 않았다.
