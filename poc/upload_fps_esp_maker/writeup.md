# FPS GAMES ESP MAKER!

## 개요
- 카테고리: Windows 게임 클라이언트 / ESP + Magic Hitbox PoC
- 대상: BloodStrike CTF 인스턴스
- 업로드 파일: `C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\BloodStrikeCTFESP_fps_esp_maker_upload.zip`

## 핵심 관찰
CTF 인스턴스의 엔티티 snapshot에서 플레이어와 봇의 월드 body bounds를 얻을 수 있다. PoC는 게임 내부 `spell_core_main.GetShootResult` / `GetShootResultWithPenetrate`가 비전투 hit 또는 miss를 반환할 때 확장된 AABB와 총알 ray를 교차시켜 synthetic `ShootEntityResult`를 반환한다.

이 hitbox PoC는 aimbot이 아니다. 조준점, 마우스, 카메라를 보정하지 않고, 현재 쏜 ray가 피부 주변의 확장 hitbox를 지나가면 봇/플레이어에 대한 material `1001` combat hit 결과를 합성한다. 따라서 피부가 아닌 가까운 영역을 쏴도 피격 판정이 생기는 방식이다.

플레이어 대상은 봇보다 검증이 엄격할 수 있으므로, 확장 AABB 교차점 자체를 damage `hit_pos`로 보내지 않는다. 확장 AABB는 “근처를 쐈는지” eligibility 판정에만 쓰고, 실제 `ShootEntityResult.raycast_bone_res.Pos`와 damage `hit_pos`는 대상의 실제 bone 좌표로 보정한다. 또한 synthetic hit 직후 `DealWeaponDamageResult` payload의 `hit_dir` / `verify_shoot_dir`도 해당 bone 방향으로 맞춰 player 검증 payload가 일관되게 보이도록 했다.

추가로 player 경로에서는 synthetic hit 생성 직후 `DealWeaponDamageResult`를 직접 호출한다. 이 호출은 원본 `SpellStrikeForRobot`/gun spell 흐름과 같은 `spell_result`, `weapon_id`, `weapon_guid`, `hit_part`, `hit_pos`, `hit_dir`, `hit_back`, `hit_penetrate`, `penetrate_materials`, `verify_start_pos`, `verify_camera_pos`, `verify_shoot_dir` payload를 사용한다. 즉 player도 단순 hit 표시가 아니라 damage/kill 처리 함수까지 타도록 한다.

대상 후보는 봇 전용이 아니다. local player를 제외한 player entity와 robot entity를 모두 수집한 뒤 enemy/team relation이 `2`인 대상에만 적용한다. 현재 실행 검증에서는 CTF 사격장에 `players=0`, `bots=6`만 존재해서 봇 로그만 남았다.

## PoC 구성
- `BloodStrikeCTFESP.exe`: C++ ESP overlay
- `remote_py_run.py`: 대상 프로세스에서 Python 코드를 실행하는 주입 러너
- `ctf_native_snapshot_code.py`: 엔티티, 카메라, 무기, 가시성 snapshot exporter
- `ctf_overlay_settings.ini`: ESP와 hitbox 기본 설정
- `run_poc.ps1`: 관리자 권한 실행 헬퍼
- `restart_hardlock.ps1`: 재시작 보조 스크립트

## 기본 설정
```ini
esp=1
tracers=1
aim=0
visible_only=1
prediction=1
fov_visible=0
hitbox=1
aim_fov_px=100
max_distance=800
hitbox_scale=3.40
```

`hitbox_scale=3.40`은 원래 body bounds보다 약 3.4배 큰 확장 피격 영역을 의미한다. 화면 overlay에는 확장 hitbox 박스를 표시하지 않고, native hook만 같은 scale을 읽어 실제 판정에 사용한다. `Insert` 컨트롤 창의 `Magic hitbox` 체크박스와 `Hitbox scale` 슬라이더로 live 조절할 수 있다.

## 재현 명령
```powershell
cd C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\upload_fps_esp_maker
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_poc.ps1 -DurationSeconds 25
```

## 검증 결과
실행 중인 CTF 인스턴스 PID `9616`에 재주입하여 후킹 설치와 synthetic hit 생성을 확인했다. 검증 스크립트는 실제 발사를 발생시키지 않고 `GetShootResult`만 호출했다.

```text
MAGIC_HITBOX_PATCH installed
native_aim=0 hitbox=1 hitbox_scale=3.40
original: target_type=null, material=0, non-combat wall hit
patched : magic_hitbox=true, target_type=RobotCombatAvatarShootingRange,
          material=1001, part='UpperTop'
player payload hardening: hit_pos uses real target bone, hit_dir/verify_shoot_dir
                          are patched toward that bone for synthetic hits
```
