# 충동이 캐릭터 시트 프롬프트 (my-character-prompt)

이미지 생성 AI에 넣을 '충동이' 캐릭터 시트(턴어라운드 시트) 요청문이다. 2026-11-19.
캐릭터 성격·세계관은 `brand/persona.md`, `김지민/brand/my-world-bible.md`를 따른다. 지어낸 설정은 (상상)으로 적었다.

## 1. 대표색

| 순서 | 색 | 색상 코드 | 쓰는 곳 | 고른 이유 |
|---|---|---|---|---|
| 1 | 폭탄 검정 | #22232A | 폭탄 모자 | 팀이 정한 색 |
| 2 | 크림 아이보리 | #FFF1DC | 몸·팔 | 말랑한 찹쌀떡 느낌. 분홍을 피해서 기존 캐릭터와 겹치지 않게 함 |
| 3 | 잔디 초록 | #6DBE5A | 발, 모자 띠 | 하늘마당 잔디 색(세계관 문서 '잔디 초록') |

- 포인트 색(아주 작게): 심지 끝 불꽃만 노을 주황 #FF8A3D. 다른 곳에는 쓰지 않는다.
- 2·3번 색은 김지민이 임의로 정한 제안이다. 팀 확인이 필요하다.

## 2. 종류

캐릭터 (기획전 「오늘의 충동」 브랜드 캐릭터, 이름: 충동이)

## 3. 외형 표

| 부위 | 모습 |
|---|---|
| 등신 | 1등신. 몸 전체가 동그란 공 하나다 |
| 몸 | 크림 아이보리색의 말랑한 공 모양. 매끈하고 무늬가 없다 |
| 얼굴 | 작다. 폭탄 모자가 잘 보이게 몸 아래쪽 절반에 모여 있다. 눈썹은 없다. 눈만 크게: 크고 동그란 까만 눈 2개(흰 반짝임 1개씩). 짧게 웃는 입, 옅은 볼터치 |
| 팔 | 몸 양옆에 붙은 작고 짧은 동그란 팔. 손가락 없음 |
| 발 | 팔보다 확실히 큰 잔디 초록색 동그란 발 2개. 몸 아래에 붙어 있다 |
| 폭탄 모자 | 머리(몸 위쪽)에 쓴 폭탄 모양 모자. 검정 반구 모양이고 몸 크기의 절반쯤으로 크게 보인다. 모자 아래 둘레에 잔디 초록 띠 1줄 |
| 심지·불꽃 | 모자 꼭대기에서 짧고 꼬불한 심지가 나오고, 끝에 작은 별 모양 노을 주황 불꽃이 튄다 |
| 표정 | 장난스럽고 밝다 (`brand/persona.md` 성격: 장난스럽다·재빠르다·활동적이다) |
| 어디서 왔나 | 충장로·동명동·ACC 주변. 평소에는 ACC 하늘마당 잔디 아래에 살다가, 누가 '하고 싶은 마음'이 생기면 튀어나온다 (상상) |

## 4. 레퍼런스에서 가져올 것 / 가져오지 않을 것

첨부한 레퍼런스 3장은 이미 있는 게임 캐릭터다. 비율과 질감만 참고하고, 모양은 가져오지 않는다.

| 레퍼런스 | 가져올 것 | 가져오지 않을 것 |
|---|---|---|
| 큰 모자를 쓴 작은 캐릭터 2명 | 머리에 큰 모자를 써서 모자가 먼저 눈에 띄는 비율 | 버섯 갓 모양, 동그란 점무늬, 조끼·원피스 옷 |
| 분홍 공 캐릭터 | 1등신 공 몸, 짧은 팔, 몸에 붙은 큰 발, 말랑한 3D 질감 | 분홍색 몸, 크고 긴 파란 눈, 크게 벌린 입 |
| 심지 달린 폭탄 캐릭터 | 폭탄 꼭대기 심지와 불꽃 | 몸 전체가 폭탄인 모양, 태엽 열쇠, 하늘색 뚜껑 고리, 주황 발 |

- 이미지 생성 AI에 레퍼런스 사진을 그대로 올리면 비슷하게 그려질 수 있다. 그래서 아래 요청문은 사진 대신 글로 비율과 질감만 설명한다.

## 5. 이미지 요청문

### 한국어

```
아래 캐릭터의 캐릭터 시트(턴어라운드 시트)를 가로로 긴 그림 한 장으로 그려줘.

[구성] 한 장 안에 그림 6개를 왼쪽부터 한 줄로 배치:
1) 전신 앞모습 2) 전신 오른쪽 옆모습 3) 전신 뒷모습 4) 전신 왼쪽 옆모습 5) 상반신(몸 위쪽 절반과 폭탄 모자) 6) 얼굴 클로즈업
여섯 그림 모두 옷·색·소품이 똑같아야 한다. 크기 비율도 같게.

[캐릭터] 이름 '충동이'. 1등신 캐릭터로, 몸 전체가 크림 아이보리색(#FFF1DC) 동그란 공 하나다.
얼굴은 작게, 몸 아래쪽 절반에 둔다. 눈썹은 없고 눈만 크게: 크고 동그란 까만 눈 2개(흰 반짝임 1개씩), 짧게 웃는 입, 옅은 볼터치.
몸 양옆에 작고 짧은 동그란 팔(손가락 없음), 몸 아래에 팔보다 훨씬 큰 잔디 초록(#6DBE5A) 동그란 발 2개.
머리 위에 검정(#22232A) 반구 모양 폭탄 모자를 쓰고 있다. 모자는 몸 절반 크기로 크고, 아래 둘레에 잔디 초록 띠 1줄.
모자 꼭대기에서 짧고 꼬불한 심지가 나오고, 끝에 작은 별 모양 주황(#FF8A3D) 불꽃.
표정은 장난스럽고 밝다.

[스타일] 말랑한 장난감 같은 부드러운 3D 렌더, 깨끗한 음영, 흰 배경, 그림 아래에 작은 라벨(앞/오른쪽/뒤/왼쪽/상반신/얼굴).
대표색은 검정·크림 아이보리·잔디 초록 세 가지, 주황은 불꽃에만 아주 작게.

[금지] 실제 사람이나 이미 있는 캐릭터를 닮지 않게 할 것.
눈썹, 분홍색 몸, 세로로 긴 파란 눈(눈은 동그란 까만 눈), 버섯 갓·점무늬 모자, 태엽 열쇠, 몸 전체가 폭탄인 모양은 넣지 말 것.
글자 로고, 배경 풍경, 추가 소품은 넣지 말 것.
```

### English (영어 이미지 AI용)

```
Draw a character turnaround sheet of the character below as ONE wide horizontal image.

[Layout] Six views in a single row, left to right:
1) full body front 2) full body right side 3) full body back 4) full body left side 5) upper body (top half of the body with the bomb hat) 6) face close-up.
All six views must have exactly the same outfit, colors and props, at a consistent scale.

[Character] Name: "Chungdong-i". A one-head-tall (chibi, 1:1) character whose whole body is a single round ball in cream ivory (#FFF1DC).
A small face on the lower half of the body. No eyebrows; only the eyes are big: two large round black eyes with one white highlight each, a short smiling mouth, faint blush.
Tiny short round arms on both sides (no fingers). Two round feet in grass green (#6DBE5A), clearly bigger than the arms, attached under the body.
On top of the head it wears a black (#22232A) half-dome bomb-shaped hat, about half the size of the body, with one grass-green band around its bottom edge.
A short curly fuse comes out of the top of the hat, ending in a small star-shaped orange (#FF8A3D) spark.
Playful, cheerful expression.

[Style] Soft, squishy toy-like 3D render, clean shading, plain white background, small labels under each view (Front / Right / Back / Left / Upper body / Face).
Main colors: black, cream ivory, grass green only; orange only as a tiny spark.

[Do not] Do not resemble any real person or any existing character.
No eyebrows, no pink body, no tall oval blue eyes (the eyes are round and black), no mushroom cap or spotted hat, no wind-up key, the body must not be a bomb itself.
No text logos, no background scenery, no extra props.
```

## 6. 확인할 것

- 2·3번 대표색(크림 아이보리·잔디 초록)은 제안이다. 팀이 다른 색을 고르면 요청문의 색상 코드만 바꾸면 된다.
- 하늘마당 잔디 아래에 산다는 설정은 (상상)이다(`김지민/brand/my-world-bible.md` 1절).
- 그림이 나오면 여섯 그림의 색·모자 크기·발 크기가 같은지, 레퍼런스 캐릭터와 닮지 않았는지 사람이 직접 확인한다.

## 출처

| 사이트 | 주소 | 확인한 날짜 |
|---|---|---|
| GitHub AXC_team5 `brand/persona.md` (1e5331b) | https://github.com/starlike2you/AXC_team5/blob/main/brand/persona.md | 2026-11-19 |
| GitHub AXC_team5 `김지민/brand/my-world-bible.md` (b3d7bd3) | https://github.com/starlike2you/AXC_team5/blob/main/김지민/brand/my-world-bible.md | 2026-11-19 |
| 사용자가 첨부한 레퍼런스 이미지 3장 (모자 쓴 작은 캐릭터 2명, 분홍 공 캐릭터, 심지 달린 폭탄 캐릭터) | 채팅 첨부 | 2026-11-19 |
