# 치과 영상 분석 자동화 프로그램 디자인 가이드

## 목차
- [디자인 시스템 개요](#디자인-시스템-개요)
- [컬러 팔레트](#컬러-팔레트)
- [페이지 구현](#페이지-구현)
- [레이아웃 컴포넌트](#레이아웃-컴포넌트)
- [인터랙션 패턴](#인터랙션-패턴)
- [반응형 브레이크포인트](#반응형-브레이크포인트)

---

## 디자인 시스템 개요

### 디자인 원칙
**미니멀하고 집중된 의료 전문가용 인터페이스**

1. **명확성 (Clarity)**: 모든 요소는 명확한 목적을 가지며, 불필요한 장식은 배제
2. **신뢰성 (Trustworthy)**: 의료 데이터를 다루는 만큼 안정적이고 전문적인 느낌 전달
3. **효율성 (Efficiency)**: 반복 작업을 최소화하는 직관적인 플로우

### 무드 & 톤
- **Clean**: 여백을 충분히 활용한 깔끔한 레이아웃
- **Focused**: 핵심 기능에 집중할 수 있는 시각적 계층 구조
- **Trustworthy**: 일관된 컬러와 타이포그래피로 전문성 표현

### 참조 디자인
- Carrd.co의 단순하고 효과적인 레이아웃 구조
- Typeform의 단계별 진행 표시와 매끄러운 전환 효과

---

## 컬러 팔레트

### TailwindCSS 컬러 시스템

#### Primary Colors (Blue)
| 변수명 | HEX 코드 | 용도 | WCAG 대비율 |
|--------|----------|------|-------------|
| `primary-50` | #EFF6FF | 배경 하이라이트 | - |
| `primary-100` | #DBEAFE | 호버 배경 | - |
| `primary-200` | #BFDBFE | 비활성 배경 | - |
| `primary-300` | #93C5FD | 보조 요소 | 3.5:1 |
| `primary-400` | #60A5FA | 보조 버튼 | 3.8:1 |
| **`primary-500`** | **#1E40AF** | **주요 액션** | **7.2:1** ✓ |
| `primary-600` | #2563EB | 호버 상태 | 4.5:1 ✓ |
| `primary-700` | #1D4ED8 | 눌림 상태 | 5.8:1 ✓ |
| `primary-800` | #1E40AF | 강조 텍스트 | 7.2:1 ✓ |
| `primary-900` | #1E3A8A | 다크 모드 | 9.1:1 ✓ |

#### Neutral Colors (Gray)
| 변수명 | HEX 코드 | 용도 | WCAG 대비율 |
|--------|----------|------|-------------|
| `gray-50` | #F9FAFB | 페이지 배경 | - |
| `gray-100` | #F3F4F6 | 카드 배경 | - |
| `gray-200` | #E5E7EB | 구분선 | - |
| `gray-300` | #D1D5DB | 비활성 테두리 | - |
| `gray-400` | #9CA3AF | 플레이스홀더 | 2.7:1 |
| `gray-500` | #6B7280 | 보조 텍스트 | 4.5:1 ✓ |
| `gray-600` | #4B5563 | 일반 텍스트 | 7.1:1 ✓ |
| `gray-700` | #374151 | 강조 텍스트 | 10.1:1 ✓ |
| `gray-800` | #1F2937 | 제목 | 13.1:1 ✓ |
| `gray-900` | #111827 | 최강조 텍스트 | 15.3:1 ✓ |

#### System Colors
| 변수명 | HEX 코드 | 용도 |
|--------|----------|------|
| `success-500` | #10B981 | 성공 메시지 |
| `warning-500` | #F59E0B | 경고 메시지 |
| `error-500` | #EF4444 | 오류 메시지 |
| `info-500` | #3B82F6 | 정보 메시지 |

### 컬러 사용 가이드라인

```css
/* Tailwind Config 예시 */
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1E40AF',
          50: '#EFF6FF',
          // ... 나머지 색상
        },
        gray: {
          // ... gray 색상
        }
      }
    }
  }
}
```

---

## 페이지 구현

### 1. 로그인 페이지

#### 핵심 목적
빠르고 안전한 인증을 통해 프로그램 접근 제공

#### 컴포넌트 구성
- 로고 및 제품명
- 이메일/비밀번호 입력 필드
- 로그인 버튼
- 자동 로그인 체크박스

#### 레이아웃
```jsx
<div className="min-h-screen bg-gray-50 flex items-center justify-center">
  <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-sm">
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-800">Web Ceph Auto</h1>
      <p className="mt-2 text-sm text-gray-500">치과 영상 분석 자동화</p>
    </div>
    <form className="mt-8 space-y-6">
      {/* 입력 필드 */}
    </form>
  </div>
</div>
```

![로그인 페이지 예시](https://picsum.photos/800/600?text=Login+Page)

### 2. 메인 대시보드

#### 핵심 목적
오늘의 처리 현황을 한눈에 파악하고 빠른 작업 시작

#### 컴포넌트 구성
- 통계 위젯 (처리 완료, 대기 중, 실패)
- 빠른 실행 버튼
- 최근 활동 목록
- 실시간 상태 표시

#### 레이아웃
```jsx
<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
  {/* 통계 카드 */}
  <div className="bg-white p-6 rounded-lg shadow-sm">
    <h3 className="text-sm font-medium text-gray-500">오늘 처리 완료</h3>
    <p className="text-3xl font-bold text-primary-500 mt-2">24</p>
  </div>
  
  {/* 빠른 실행 */}
  <div className="lg:col-span-2">
    <button className="w-full py-4 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors">
      신규 환자 처리 시작
    </button>
  </div>
</div>
```

![대시보드 예시](https://picsum.photos/1200/800?text=Dashboard)

### 3. 환자 정보 입력

#### 핵심 목적
정확한 환자 정보를 효율적으로 입력

#### 컴포넌트 구성
- 단계별 진행 표시기
- 폼 필드 그룹
- 실시간 검증 메시지
- 이전/다음 버튼

#### 상태별 스타일
| 상태 | 클래스 | 설명 |
|------|--------|------|
| 기본 | `border-gray-300` | 일반 입력 필드 |
| 포커스 | `border-primary-500 ring-2 ring-primary-200` | 입력 중 |
| 오류 | `border-error-500` | 검증 실패 |
| 성공 | `border-success-500` | 검증 통과 |
| 비활성 | `bg-gray-100 cursor-not-allowed` | 입력 불가 |

### 4. 자동화 진행 화면

#### 핵심 목적
자동화 프로세스의 진행 상황을 실시간으로 모니터링

#### 컴포넌트 구성
```jsx
<div className="space-y-4">
  {/* 전체 진행률 */}
  <div className="bg-white p-6 rounded-lg shadow-sm">
    <div className="flex justify-between mb-2">
      <span className="text-sm font-medium text-gray-700">전체 진행률</span>
      <span className="text-sm text-gray-500">3/5 단계</span>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div className="bg-primary-500 h-2 rounded-full transition-all duration-300" style={{width: '60%'}}></div>
    </div>
  </div>
  
  {/* 단계별 상태 */}
  <div className="bg-white p-6 rounded-lg shadow-sm">
    {steps.map((step, index) => (
      <div key={index} className="flex items-center space-x-4 py-3">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
          step.completed ? 'bg-success-500 text-white' : 
          step.active ? 'bg-primary-500 text-white animate-pulse' : 
          'bg-gray-200 text-gray-400'
        }`}>
          {/* 아이콘 */}
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-800">{step.name}</p>
          <p className="text-xs text-gray-500">{step.status}</p>
        </div>
      </div>
    ))}
  </div>
</div>
```

![진행 화면 예시](https://picsum.photos/1200/800?text=Progress+Monitor)

---

## 레이아웃 컴포넌트

### 1. 기본 레이아웃 구조

```jsx
const MainLayout = ({ children }) => {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* 사이드바 */}
      <aside className="w-64 bg-white shadow-sm">
        <div className="p-4">
          <h1 className="text-xl font-bold text-gray-800">Web Ceph Auto</h1>
        </div>
        <nav className="mt-8">
          {/* 네비게이션 아이템 */}
        </nav>
      </aside>
      
      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
};
```

### 2. 반응형 네비게이션

| 브레이크포인트 | 레이아웃 변경 |
|---------------|--------------|
| Mobile (< 768px) | 햄버거 메뉴, 전체 화면 오버레이 |
| Tablet (768px - 1023px) | 축소된 사이드바 (아이콘만) |
| Desktop (≥ 1024px) | 전체 사이드바 표시 |

### 3. 카드 컴포넌트

```jsx
const Card = ({ title, children, actions }) => (
  <div className="bg-white rounded-lg shadow-sm p-6">
    {title && (
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-800">{title}</h3>
        {actions && <div>{actions}</div>}
      </div>
    )}
    <div>{children}</div>
  </div>
);
```

### 4. 버튼 컴포넌트 변형

```jsx
// Primary Button
<button className="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors">
  주요 액션
</button>

// Secondary Button
<button className="px-4 py-2 bg-white text-primary-500 border border-primary-500 rounded-md hover:bg-primary-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors">
  보조 액션
</button>

// Ghost Button
<button className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors">
  텍스트 버튼
</button>
```

---

## 인터랙션 패턴

### 1. 로딩 상태

```jsx
// 스켈레톤 로딩
<div className="animate-pulse">
  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
</div>

// 스피너
<div className="flex items-center justify-center p-4">
  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
</div>
```

### 2. 토스트 알림

```jsx
const Toast = ({ type, message }) => {
  const colors = {
    success: 'bg-success-500',
    error: 'bg-error-500',
    warning: 'bg-warning-500',
    info: 'bg-info-500'
  };

  return (
    <div className={`${colors[type]} text-white px-6 py-4 rounded-lg shadow-lg flex items-center space-x-3`}>
      <Icon type={type} />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
};
```

### 3. 모달 다이얼로그

```jsx
<div className="fixed inset-0 z-50 overflow-y-auto">
  <div className="flex items-center justify-center min-h-screen p-4">
    {/* 배경 오버레이 */}
    <div className="fixed inset-0 bg-black bg-opacity-25 transition-opacity"></div>
    
    {/* 모달 콘텐츠 */}
    <div className="relative bg-white rounded-lg max-w-md w-full p-6 shadow-xl">
      <h3 className="text-lg font-medium text-gray-800 mb-4">모달 제목</h3>
      <p className="text-sm text-gray-600 mb-6">모달 내용</p>
      <div className="flex justify-end space-x-3">
        <button className="px-4 py-2 text-gray-600 hover:text-gray-800">취소</button>
        <button className="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600">확인</button>
      </div>
    </div>
  </div>
</div>
```

### 4. 폼 검증 피드백

```jsx
<div className="space-y-1">
  <input 
    className="w-full px-3 py-2 border border-error-500 rounded-md focus:ring-2 focus:ring-error-200"
    type="text"
  />
  <p className="text-xs text-error-500">필수 입력 항목입니다</p>
</div>
```

### 5. 애니메이션 전환

```css
/* 페이드 인/아웃 */
.fade-enter {
  opacity: 0;
  transition: opacity 200ms ease-in-out;
}
.fade-enter-active {
  opacity: 1;
}

/* 슬라이드 업 */
.slide-up {
  transform: translateY(10px);
  opacity: 0;
  transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-up-active {
  transform: translateY(0);
  opacity: 1;
}
```

---

## 반응형 브레이크포인트

### 브레이크포인트 정의

```scss
$breakpoints: (
  'mobile': 320px,
  'tablet': 768px,
  'desktop': 1024px,
  'wide': 1440px
);
```

### Tailwind CSS 매핑

| 디바이스 | 브레이크포인트 | Tailwind 접두사 | 용도 |
|----------|---------------|----------------|------|
| Mobile | 320px - 767px | 기본 (접두사 없음) | 모바일 우선 디자인 |
| Tablet | 768px - 1023px | `md:` | 태블릿 레이아웃 |
| Desktop | 1024px - 1439px | `lg:` | 데스크톱 표준 |
| Wide | 1440px 이상 | `xl:` | 와이드 스크린 |

### 반응형 그리드 시스템

```jsx
// 반응형 그리드 예시
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  {/* 그리드 아이템 */}
</div>

// 반응형 패딩
<div className="p-4 md:p-6 lg:p-8">
  {/* 콘텐츠 */}
</div>

// 반응형 폰트 크기
<h1 className="text-xl md:text-2xl lg:text-3xl font-bold">
  반응형 제목
</h1>
```

### 디바이스별 레이아웃 변경

```jsx
// Mobile: 스택 레이아웃
// Tablet: 2열 그리드
// Desktop: 사이드바 + 메인 콘텐츠
<div className="flex flex-col md:grid md:grid-cols-2 lg:flex lg:flex-row">
  <aside className="w-full lg:w-64">
    {/* 사이드바 */}
  </aside>
  <main className="flex-1">
    {/* 메인 콘텐츠 */}
  </main>
</div>
```

### 터치 타겟 사이즈

| 요소 | 최소 크기 | Tailwind 클래스 |
|------|----------|----------------|
| 버튼 | 44x44px | `min-h-[44px] min-w-[44px]` |
| 링크 | 44x44px | `p-3` (최소 패딩) |
| 입력 필드 | 44px 높이 | `h-11` |
| 체크박스/라디오 | 24x24px | `w-6 h-6` |

---

## WCAG 2.2 접근성 체크리스트

### 컬러 대비율
- [x] 일반 텍스트: 4.5:1 이상
- [x] 큰 텍스트 (18pt+): 3:1 이상
- [x] UI 컴포넌트: 3:1 이상
- [x] 포커스 인디케이터: 3:1 이상

### 키보드 접근성
- [x] 모든 인터랙티브 요소 Tab 키로 접근 가능
- [x] 포커스 순서가 논리적
- [x] 포커스 상태 시각적으로 명확
- [x] 키보드 트랩 없음

### 스크린 리더 지원
- [x] 의미 있는 alt 텍스트
- [x] 적절한 ARIA 레이블
- [x] 헤딩 계층 구조 준수
- [x] 폼 레이블 연결

### 반응형 디자인
- [x] 320px 최소 너비 지원
- [x] 200% 확대 시에도 가로 스크롤 없음
- [x] 터치 타겟 최소 44x44px

---

*이 디자인 가이드는 지속적으로 업데이트되며, 사용자 피드백과 접근성 개선 사항을 반영하여 발전시켜 나갈 예정입니다.*