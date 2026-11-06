# EvalCheck

**모델 점수를 믿기 전에, 데이터 분할부터 확인하세요.**

Jupyter 노트북·Python 코드의 평가 위험 흐름과 CSV·JSONL 데이터의 겹침을 함께 검사하는 로컬 Python 도구다. API 키와 실행 의존성이 없으며, 결과를 검색 가능한 HTML 보고서와 JSON으로 저장한다.

현재 버전은 **0.5.0 사전 공개본**이다. PyPI에는 배포하지 않았으며 `evalcheck-local`은 임시 배포 이름이다. 저장소 디렉터리에서 설치한다.

```bash
python -m pip install .
evalcheck demo --out my-demo
```

`my-demo/report.html`을 열면 의도적으로 오류를 심어 놓은 합성 데이터의 검사 결과를 볼 수 있다.

```bash
evalcheck audit \
  --split train=train.csv --split test=test.csv \
  --text answer --label grade --group question_id \
  --out my-audit
```

| 검사 | 의미 |
|---|---|
| 정확 중복 | 유니코드·대소문자·공백을 정규화한 동일 텍스트가 여러 분할에 존재 |
| 유사 중복 | 서로 다른 분할의 토큰 집합 Jaccard 유사도가 기준 이상 |
| 그룹 겹침 | 분리하도록 지정한 문항·환자·문서 등의 식별자가 여러 분할에 존재 |
| 라벨 충돌 | 정규화한 같은 텍스트에 서로 다른 라벨이 부여됨 |

문항이 다르면 같은 답안의 점수가 다를 수 있다. 그룹을 공유하는 평가가 적절한 과제도 있다. 따라서 결과는 검토 근거이며, 누출을 단정하거나 라벨을 자동 수정하지 않는다.

새 분할을 제안하려면 다음을 실행한다.

```bash
evalcheck split all.jsonl --group question_id --out proposed-split
```

원본 행을 삭제하지 않고, 동일 텍스트·동일 그룹·유사 텍스트가 연결된 묶음을 함께 배정한다. 요청 비율과 실제 비율, 각 행의 배정과 사후 감사 결과를 남긴다. 기존 공식 벤치마크의 분할을 임의로 바꾸는 용도로 사용하면 안 된다. 클래스 비율은 자동 보정하지 않는다.

합성 그룹 암기 실험도 재현할 수 있다.

```bash
python -m pip install '.[experiment]'
python examples/compare_splits.py
```

이 배포본에서 5개 시드의 평균 정확도는 행 단위 무작위 분할 100%, 그룹 단위 홀드아웃 43%였다. 그룹마다 임의의 라벨을 부여한 합성 과제에서 측정한 값이며 실제 서비스 성능은 아니다.

검사가 예산을 초과하면 `incomplete`와 종료 코드 `3`을 반환한다. 완료된 검사도 의미적 유사성, 시간 누출, 정답에서 파생한 특성, 모델 선택 과정의 누출은 확인하지 못한다. HTML 보고서는 원문 증거를 포함한다.

실제 공개 데이터 검증도 포함했다. UCI의 감성분석 문장 3,000개에 우리가 만든 시드 42의 80:20 무작위 분할을 적용했을 때, 정확 중복 7개 묶음과 유사 문장 7쌍에 총 25개 행이 관련됐다. 연결된 문장을 함께 배정한 새 제안에서는 같은 기준의 교차 겹침이 0건이었고 3,000개 행을 모두 보존했다. 두 분할의 시험 문항은 다르며, 모델 성능 향상이나 기존 연구 오류를 입증한 결과는 아니다.

```bash
python examples/uci_sentiment/reproduce.py --out my-uci-case
```

이 재현은 인터넷 연결 없이 실행되며, 원본 파일의 해시를 확인한다. `--id-column source_id`를 쓰면 각 증거에 원본 파일명과 줄 번호를 남길 수 있다. [사례 문서](examples/uci_sentiment/README.md)에 프로토콜·해석·출처를 정리했다. 소프트웨어는 MIT, 포함된 UCI 데이터는 CC BY 4.0이다.

테스트:

```bash
python -m unittest discover -s tests -v
```

전체 API·출력·한계는 [영문 README](README.md), [방법론](docs/methodology.md), [출시 계획](docs/release-plan.md)을 참고한다.

실제 모델 비교도 수행했다. 연결된 문장을 분리하지 않은 학습 1,800개·개발 600개·테스트 600개를 고정하고, 개발 데이터에서 세 후보 중 모델을 골랐다. 같은 테스트에서 기준 모델의 Macro-F1은 0.7949, 선택 후보는 0.8033이었다. 차이는 +0.0084지만 95% 구간 [-0.0164, +0.0320]이 0을 포함하므로 뚜렷한 개선이 입증됐다고 표현하지 않는다. 이 비교는 모델의 특성 표현을 바꾼 효과를 측정하며, 감사 도구 자체가 정확도를 높인다는 인과적 근거는 아니다.

```bash
python -m pip install '.[experiment]'
python examples/uci_sentiment/train_models.py --out my-model-experiment
```

분석 계획·개발 점수·선택 기록·테스트 예측·불확실성은 [모델 비교 문서](examples/uci_sentiment/model_experiment/README.md)에 정리했다. 테스트 결과를 보고 후보를 다시 고르지 않았다.

노트북 검사와 설치 없는 브라우저 체험판을 추가했다.

```bash
evalcheck scan examples/notebooks/leaky.ipynb --out my-code-audit --fail-on none
```

`web/index.html`을 다운로드해 브라우저로 열면 같은 Python 엔진을 WebAssembly로 실행한다. 첫 검사에서는 인터넷으로 고정 버전 런타임을 받으며, 입력 파일 내용은 애플리케이션 서버로 보내지 않는다. 대상 노트북 코드는 실행하지 않고 AST로 분석한다.

지원 규칙은 분할 전 전처리 학습, 시험 데이터로 fit, 교차검증 전 전체 특성 학습, 분할 전 리샘플링이다. 원인과 사용 지점의 셀·줄 번호를 함께 제시한다. 함수 본문·조건문·사용자 정의 도우미 등은 놓칠 수 있고 분석 범위 메모에 명시한다.

고정한 합성 잡음 실험 10회에서는 분할 전 특성 선택으로 평균 79.5%의 과장된 점수가 나왔고, 학습 데이터에서만 선택한 Pipeline은 51.6%였다. 이는 실제 모델을 개선한 결과가 아니라, 신호가 없는 자료에서 평가 점수가 부풀 수 있음을 재현한 결과다. 자체 작성 40개 검증 사례에서는 위험 24개 중 20개를 탐지했고 정상 16개에 오탐이 없었다. 놓친 4개는 전체 재현율 계산에 포함했다. 외부 노트북의 일반 탐지 성능으로 주장하지 않는다.

pre-commit과 GitHub Actions용 설정, HTML·JSON·SARIF 출력도 포함했다. 실제 GitHub 서버에서의 실행·업로드와 공개 배포는 아직 수행하지 않았다.

## 한국어 / English

체험판 상단에서 **한국어 / English**를 전환한다. 처음에는 브라우저 언어를 따르고 이후 선택을 기억한다. 입력과 검사 결과는 유지되며 안내·결과 설명·검색 안내가 바뀐다. HTML 내보내기는 선택한 언어를 사용한다.

```bash
evalcheck scan notebooks --out audit-ko --lang ko
evalcheck demo --out demo-en --lang en
```

`audit`, `split`, `scan`, `demo`에 `--lang ko|en`을 사용할 수 있다. 기본값은 `en`이다. Python에서는 `write_report(..., lang="ko")`, `write_code_report(..., lang="ko")`를 사용한다. 원문·코드·식별자·JSON/SARIF·검사 판정은 번역하지 않는다. 한국어 UI는 의미 기반 한국어 유사도 모델을 추가한 기능이 아니다.
