(() => {
  const BASE_STRINGS = {
    stepDetails: "Trip Details",
    stepDestinations: "Suggested Destinations",
    stepAccount: "Account Required",
    stepPlans: "Plan Options",
    stepComplete: "Plan Confirmed",
    titleDetails: "Build your travel plan",
    subtitleDetails: "Choose dates, guests, budget, and activities. Phase 1 creates an AI itinerary only — no hotel or tour booking yet.",
    titleDestinations: "Pick your destination",
    subtitleDestinations: "These cities are suggested by AI according to the details you entered.",
    titleAccount: "Sign in to continue",
    subtitleAccount: "Your draft is safe. Authenticate now and continue from the selected destination.",
    titlePlans: "Review generated plan options",
    subtitlePlans: "Compare the two AI itineraries. This is a plan suggestion, not a reservation.",
    titleComplete: "Your plan is active",
    subtitleComplete: "Your confirmed itinerary is ready. You can open the full day-by-day plan from your account.",
    datesLabel: "Travel dates",
    startDate: "Start date",
    endDate: "End date",
    adults: "Adults",
    children: "Children",
    budgetLabel: "Budget",
    budgetCheap: "Cheap",
    budgetEconomy: "Economy",
    budgetLuxury: "Luxury",
    activitiesLabel: "Activities",
    activitiesHint: "Pick at least one activity.",
    hotelNameLabel: "Hotel name",
    hotelNamePlaceholder: "Optional",
    hotelNameHint: "If you already have a stay, we will plan around it. This is not a booking.",
    findDestinations: "Find destinations",
    back: "Back",
    selectDestination: "Select this destination",
    loadingCities: "We are asking AI for the best matching destinations...",
    noCities: "No destination suggestions were returned. Try adjusting your dates, budget, or activities.",
    signInToContinue: "Sign In",
    signUpToContinue: "Sign Up",
    close: "Close",
    selectedDestination: "Selected destination",
    destinationDescription: "Why this city fits",
    validationMessage: "Complete travel dates and select at least one activity.",
    validationDateOrder: "End date cannot be earlier than start date.",
    draftRestored: "Your saved draft has been restored.",
    syncFailed: "Your local draft is safe, but server sync could not be completed right now.",
    loadActivitiesFailed: "Activities could not be loaded right now.",
    generatingPlans: "Generating plan options...",
    retryGenerate: "Try generating again",
    confirmPlan: "Confirm this plan",
    estimatedTotal: "Estimated total",
    loadingPlan: "Preparing your final itinerary...",
    goToAccount: "Go to account",
    createAnotherPlan: "Create another plan",
    noActivePlan: "Plan options could not be created yet. Try again or pick another destination.",
    serverDraftLoaded: "Your account draft was loaded.",
    genericError: "Something went wrong. Please try again.",
    guestsLabel: "Guests",
    dayLabel: "Day",
    planIdLabel: "Plan ID",
    optionLabel: "Option",
    viewDetails: "View details",
    viewDetailsHint: "See full trip details in your account",
  };

  const STRINGS = {
    en: BASE_STRINGS,
    tr: {
      ...BASE_STRINGS,
      stepDetails: "Seyahat Detayları",
      stepDestinations: "Önerilen Destinasyonlar",
      stepAccount: "Hesap Gerekli",
      stepPlans: "Plan Seçenekleri",
      stepComplete: "Plan Onaylandı",
      titleDetails: "Seyahat planını oluştur",
      subtitleDetails: "Tarih, misafir, bütçe ve aktiviteleri seç. Faz 1 yalnızca AI tatil planı üretir; otel ve tur rezervasyonu yok.",
      titleDestinations: "Destinasyonunu seç",
      subtitleDestinations: "Bu şehirler girdiğin tercihlere göre yapay zeka tarafından önerildi.",
      titleAccount: "Devam etmek için giriş yap",
      subtitleAccount: "Taslağın güvende. Şimdi giriş yap veya üye ol; seçtiğin destinasyondan devam et.",
      titlePlans: "Üretilen plan seçeneklerini incele",
      subtitlePlans: "İki AI itinerary'yi karşılaştır. Bu bir plan önerisidir, rezervasyon değildir.",
      titleComplete: "Planın aktif",
      subtitleComplete: "Onaylanan rota hazır. Günlük detayı hesabından açabilirsin.",
      datesLabel: "Seyahat tarihleri",
      startDate: "Başlangıç tarihi",
      endDate: "Bitiş tarihi",
      adults: "Yetişkin",
      children: "Çocuk",
      budgetLabel: "Bütçe",
      budgetCheap: "Uygun",
      budgetEconomy: "Ekonomik",
      budgetLuxury: "Lüks",
      activitiesLabel: "Aktiviteler",
      activitiesHint: "En az bir aktivite seç.",
      hotelNameLabel: "Otel adı",
      hotelNamePlaceholder: "İsteğe bağlı",
      hotelNameHint: "Zaten bir konaklaman varsa planı onun etrafında kurarız. Bu bir rezervasyon değildir.",
      findDestinations: "Destinasyon bul",
      back: "Geri",
      selectDestination: "Bu destinasyonu seç",
      loadingCities: "Yapay zekadan sana uygun destinasyonlar alınıyor...",
      noCities: "Destinasyon önerisi dönmedi. Tarih, bütçe veya aktiviteleri güncelleyip tekrar dene.",
      signInToContinue: "Giriş Yap",
      signUpToContinue: "Kayıt Ol",
      close: "Kapat",
      selectedDestination: "Seçilen destinasyon",
      destinationDescription: "Bu şehrin uygun olma nedeni",
      validationMessage: "Seyahat tarihlerini doldur ve en az bir aktivite seç.",
      validationDateOrder: "Bitiş tarihi başlangıç tarihinden önce olamaz.",
      draftRestored: "Kaydedilmiş taslağın geri yüklendi.",
      syncFailed: "Yerel taslağın güvende, ancak sunucuya senkronizasyon şu anda tamamlanamadı.",
      loadActivitiesFailed: "Aktiviteler şu anda yüklenemedi.",
      generatingPlans: "Plan seçenekleri üretiliyor...",
      retryGenerate: "Tekrar dene",
      confirmPlan: "Bu planı onayla",
      estimatedTotal: "Tahmini toplam",
      loadingPlan: "Final rota hazırlanıyor...",
      goToAccount: "Hesaba git",
      createAnotherPlan: "Yeni plan oluştur",
      noActivePlan: "Plan seçenekleri henüz oluşturulamadı. Tekrar dene veya başka destinasyon seç.",
      serverDraftLoaded: "Hesabındaki taslak yüklendi.",
      genericError: "Bir sorun oluştu. Lütfen tekrar dene.",
      guestsLabel: "Misafir",
      dayLabel: "Gün",
      planIdLabel: "Plan ID",
      optionLabel: "Seçenek",
      viewDetails: "Detayı Gör",
      viewDetailsHint: "Tüm gezi detaylarını hesabında incele",
    },
    ru: {
      ...BASE_STRINGS,
      stepDetails: "Детали поездки",
      stepDestinations: "Рекомендуемые направления",
      stepAccount: "Требуется аккаунт",
      stepPlans: "Варианты плана",
      stepComplete: "План подтвержден",
      titleDetails: "Соберите свой план поездки",
      subtitleDetails: "Выберите даты, гостей, бюджет и активности. Фаза 1 создает только AI-маршрут — без бронирования отеля и туров.",
      titleDestinations: "Выберите направление",
      subtitleDestinations: "Эти города предложены ИИ на основе ваших предпочтений.",
      titleAccount: "Войдите, чтобы продолжить",
      subtitleAccount: "Ваш черновик сохранен. Авторизуйтесь и продолжите с выбранного направления.",
      titlePlans: "Проверьте варианты маршрута",
      subtitlePlans: "Сравните два маршрута ИИ. Это предложение плана, а не бронирование.",
      titleComplete: "Ваш план активен",
      subtitleComplete: "Подтвержденный маршрут готов. Полное расписание можно открыть в аккаунте.",
      datesLabel: "Даты поездки",
      startDate: "Дата начала",
      endDate: "Дата окончания",
      adults: "Взрослые",
      children: "Дети",
      budgetLabel: "Бюджет",
      budgetCheap: "Бюджетный",
      budgetEconomy: "Стандарт",
      budgetLuxury: "Люкс",
      activitiesLabel: "Активности",
      activitiesHint: "Выберите хотя бы одну активность.",
      hotelNameLabel: "Название отеля",
      hotelNamePlaceholder: "Необязательно",
      hotelNameHint: "Если жилье уже есть, маршрут будет построен вокруг него. Это не бронирование.",
      findDestinations: "Найти направления",
      back: "Назад",
      selectDestination: "Выбрать это направление",
      loadingCities: "ИИ подбирает для вас лучшие направления...",
      noCities: "Подходящие направления не найдены. Попробуйте изменить даты, бюджет или активности.",
      signInToContinue: "Войти",
      signUpToContinue: "Регистрация",
      close: "Закрыть",
      selectedDestination: "Выбранное направление",
      destinationDescription: "Почему этот город подходит",
      validationMessage: "Заполните даты поездки и выберите хотя бы одну активность.",
      validationDateOrder: "Дата окончания не может быть раньше даты начала.",
      draftRestored: "Ваш сохраненный черновик восстановлен.",
      syncFailed: "Локальный черновик сохранен, но синхронизация с сервером сейчас недоступна.",
      loadActivitiesFailed: "Сейчас не удалось загрузить активности.",
      generatingPlans: "Создаем варианты плана...",
      retryGenerate: "Попробовать снова",
      confirmPlan: "Подтвердить этот план",
      estimatedTotal: "Ориентировочная стоимость",
      loadingPlan: "Подготавливаем итоговый маршрут...",
      goToAccount: "Перейти в аккаунт",
      createAnotherPlan: "Создать новый план",
      noActivePlan: "Варианты плана пока не созданы. Попробуйте снова или выберите другое направление.",
      serverDraftLoaded: "Черновик из аккаунта загружен.",
      genericError: "Что-то пошло не так. Попробуйте еще раз.",
      guestsLabel: "Гости",
      dayLabel: "День",
      planIdLabel: "ID плана",
      optionLabel: "Вариант",
      viewDetails: "Смотреть детали",
      viewDetailsHint: "Откройте полный маршрут в аккаунте",
    },
    ar: {
      ...BASE_STRINGS,
      stepDetails: "تفاصيل الرحلة",
      stepDestinations: "الوجهات المقترحة",
      stepAccount: "الحساب مطلوب",
      stepPlans: "خيارات الخطة",
      stepComplete: "تم تأكيد الخطة",
      titleDetails: "أنشئ خطة رحلتك",
      subtitleDetails: "اختر التواريخ والضيوف والميزانية والأنشطة. المرحلة 1 تنشئ مسار رحلة بالذكاء الاصطناعي فقط دون حجز فندق أو جولات.",
      titleDestinations: "اختر وجهتك",
      subtitleDestinations: "هذه المدن تم اقتراحها بالذكاء الاصطناعي بناء على تفضيلاتك.",
      titleAccount: "سجل الدخول للمتابعة",
      subtitleAccount: "مسودتك محفوظة. قم بتسجيل الدخول أو إنشاء حساب ثم تابع من الوجهة التي اخترتها.",
      titlePlans: "راجع خيارات الخطة",
      subtitlePlans: "قارن بين المسارين. هذه توصية خطة وليست حجزا.",
      titleComplete: "خطتك أصبحت جاهزة",
      subtitleComplete: "المسار المؤكد جاهز. يمكنك فتح التفاصيل اليومية من حسابك.",
      datesLabel: "تواريخ الرحلة",
      startDate: "تاريخ البداية",
      endDate: "تاريخ النهاية",
      adults: "البالغون",
      children: "الأطفال",
      budgetLabel: "الميزانية",
      budgetCheap: "اقتصادي جدا",
      budgetEconomy: "اقتصادي",
      budgetLuxury: "فاخر",
      activitiesLabel: "الأنشطة",
      activitiesHint: "اختر نشاطا واحدا على الأقل.",
      hotelNameLabel: "اسم الفندق",
      hotelNamePlaceholder: "اختياري",
      hotelNameHint: "إذا كان لديك إقامة مسبقا فسنبني الخطة حولها. هذا ليس حجزا.",
      findDestinations: "ابحث عن وجهات",
      back: "رجوع",
      selectDestination: "اختر هذه الوجهة",
      loadingCities: "الذكاء الاصطناعي يبحث عن أفضل الوجهات المناسبة لك...",
      noCities: "لم يتم العثور على وجهات مناسبة. جرّب تعديل التواريخ أو الميزانية أو الأنشطة.",
      signInToContinue: "تسجيل الدخول",
      signUpToContinue: "إنشاء حساب",
      close: "إغلاق",
      selectedDestination: "الوجهة المختارة",
      destinationDescription: "لماذا هذه المدينة مناسبة",
      validationMessage: "أكمل تواريخ الرحلة واختر نشاطا واحدا على الأقل.",
      validationDateOrder: "لا يمكن أن يكون تاريخ النهاية قبل تاريخ البداية.",
      draftRestored: "تمت استعادة المسودة المحفوظة.",
      syncFailed: "مسودتك المحلية محفوظة، لكن تعذر مزامنتها مع الخادم الآن.",
      loadActivitiesFailed: "تعذر تحميل الأنشطة الآن.",
      generatingPlans: "جار إنشاء خيارات الخطة...",
      retryGenerate: "حاول مرة أخرى",
      confirmPlan: "أكد هذه الخطة",
      estimatedTotal: "الإجمالي التقديري",
      loadingPlan: "جار تجهيز خط السير النهائي...",
      goToAccount: "اذهب إلى الحساب",
      createAnotherPlan: "أنشئ خطة جديدة",
      noActivePlan: "تعذر إنشاء خيارات الخطة. حاول مرة أخرى أو اختر وجهة أخرى.",
      serverDraftLoaded: "تم تحميل المسودة من حسابك.",
      genericError: "حدث خطأ ما. حاول مرة أخرى.",
      guestsLabel: "الضيوف",
      dayLabel: "اليوم",
      planIdLabel: "معرف الخطة",
      optionLabel: "الخيار",
      viewDetails: "عرض التفاصيل",
      viewDetailsHint: "شاهد تفاصيل الرحلة كاملة في حسابك",
    },
  };

  const API_BASE = "/api/v1";
  const DRAFT_KEY = "turquaway-plan-draft";
  const RESUME_KEY = "turquaway-plan-resume";
  const EMPTY_DRAFT = {
    start_date: "",
    end_date: "",
    adults: 2,
    children: 0,
    budget_type: "economy",
    activities: [],
    language: "en",
    suggestions: [],
    city: "",
    city_description: "",
    selected_hotel_name: "",
    plan_options: [],
    confirmed_plan_id: "",
  };

  const modal = document.getElementById("plan-modal");
  const modalBody = document.getElementById("plan-modal-body");
  const modalFeedback = document.getElementById("plan-modal-feedback");
  const modalTitle = document.getElementById("plan-modal-title");
  const modalSubtitle = document.getElementById("plan-modal-subtitle");
  const modalStepLabel = document.getElementById("plan-modal-step-label");
  const closeBtn = document.getElementById("plan-modal-close");
  const openBtn = document.getElementById("nav-create-plan-btn");
  const openMobileBtn = document.getElementById("nav-mobile-create-plan");

  if (!modal || !modalBody || !modalTitle || !modalSubtitle || !modalStepLabel) {
    return;
  }

  const state = {
    step: "details",
    draft: normalizeDraft(loadRawDraft()),
    activities: [],
    activitiesLoaded: false,
    loadingSuggestions: false,
    generatingPlans: false,
    confirmingPlanId: "",
    syncing: false,
    feedback: "",
    feedbackType: "error",
    authRedirectInFlight: false,
  };

  function getLang() {
    const stored = localStorage.getItem("turquaway-language");
    return stored && STRINGS[stored] ? stored : "en";
  }

  function text(key) {
    const lang = getLang();
    return STRINGS[lang]?.[key] || STRINGS.en[key] || key;
  }

  function loadRawDraft() {
    try {
      return JSON.parse(localStorage.getItem(DRAFT_KEY) || "{}");
    } catch (_) {
      return {};
    }
  }

  function normalizeDraft(raw) {
    return {
      ...EMPTY_DRAFT,
      ...(raw || {}),
      activities: Array.isArray(raw?.activities) ? raw.activities : [],
      suggestions: Array.isArray(raw?.suggestions) ? raw.suggestions : [],
      plan_options: Array.isArray(raw?.plan_options) ? raw.plan_options : [],
      selected_hotel_name: String(raw?.selected_hotel_name || "").trim(),
      language: raw?.language || getLang(),
    };
  }

  function saveDraft() {
    state.draft.language = getLang();
    localStorage.setItem(DRAFT_KEY, JSON.stringify({
      ...EMPTY_DRAFT,
      ...state.draft,
    }));
  }

  function clearAfterPreferences() {
    state.draft.suggestions = [];
    state.draft.city = "";
    state.draft.city_description = "";
    state.draft.plan_options = [];
    state.draft.confirmed_plan_id = "";
  }

  function clearAfterCity() {
    state.draft.plan_options = [];
    state.draft.confirmed_plan_id = "";
  }

  function hasAuth() {
    return Boolean(localStorage.getItem("tw_access"));
  }

  function authHeaders() {
    const token = localStorage.getItem("tw_access");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  function clearStoredAuth() {
    localStorage.removeItem("tw_access");
    localStorage.removeItem("tw_refresh");
    localStorage.removeItem("tw_user");
  }

  function hasMeaningfulDraft() {
    return Boolean(
      state.draft.start_date ||
      state.draft.end_date ||
      state.draft.activities.length ||
      state.draft.city ||
      state.draft.plan_options.length ||
      state.draft.confirmed_plan_id
    );
  }

  function computeStep() {
    if (state.draft.confirmed_plan_id) return "complete";
    if (state.draft.plan_options.length) return "plans";
    if (state.draft.city) return hasAuth() ? "plans" : "account";
    if (state.draft.suggestions.length) return "destinations";
    return "details";
  }

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function guestSummary() {
    const adults = Number(state.draft.adults || 0);
    const children = Number(state.draft.children || 0);
    return `${adults} ${text("adults")} · ${children} ${text("children")}`;
  }

  function setFeedback(message, type = "error") {
    state.feedback = message || "";
    state.feedbackType = type;
    if (!message) {
      modalFeedback.className = "mx-auto mb-6 hidden w-full max-w-6xl border border-rose-300/40 bg-rose-950/20 px-4 py-3 text-sm text-slate-100";
      modalFeedback.textContent = "";
      return;
    }
    modalFeedback.className = `mx-auto mb-6 w-full max-w-6xl border px-4 py-3 text-sm text-slate-100 ${
      type === "success" ? "border-emerald-200/40 bg-emerald-950/20" : "border-rose-300/40 bg-rose-950/20"
    }`;
    modalFeedback.textContent = message;
  }

  function showLocalError(error) {
    setFeedback(error?.message || text("genericError"));
    render();
  }

  function closeModal() {
    modal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  }

  function resetMobileMenu() {
    const mobileMenu = document.getElementById("nav-mobile-menu");
    const hamburger = document.getElementById("nav-hamburger");
    mobileMenu?.classList.add("hidden");
    if (hamburger) {
      hamburger.setAttribute("aria-expanded", "false");
      hamburger.querySelectorAll(".hamburger-bar").forEach((bar) => {
        bar.style.transform = "";
        bar.style.opacity = "";
      });
    }
  }

  async function apiRequest(path, options = {}, authRequired = true) {
    const headers = {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(authRequired ? authHeaders() : {}),
      ...(options.headers || {}),
    };
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (response.status === 401 && authRequired) {
        clearStoredAuth();
        if (!state.authRedirectInFlight) {
          state.authRedirectInFlight = true;
          redirectToAuth("/login/");
        }
      }
      const error = new Error(payload.detail || text("genericError"));
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return payload;
  }

  async function loadServerDraftIfNeeded() {
    if (!hasAuth() || hasMeaningfulDraft()) return;
    try {
      const payload = await apiRequest("/funnel/draft/", { method: "GET" });
      state.draft = normalizeDraft({
        ...state.draft,
        start_date: payload.start_date || "",
        end_date: payload.end_date || "",
        adults: payload.adults || 2,
        children: payload.children || 0,
        budget_type: payload.budget_type || "economy",
        activities: payload.activities || [],
        language: payload.language || getLang(),
      });
      if (payload.start_date || payload.end_date || (payload.activities || []).length) {
        setFeedback(text("serverDraftLoaded"), "success");
      }
      saveDraft();
    } catch (_) {
      // Local draft remains source of truth.
    }
  }

  async function ensureActivitiesLoaded() {
    if (state.activitiesLoaded) return;
    try {
      const response = await fetch(`${API_BASE}/activities/?lang=${encodeURIComponent(getLang())}`);
      if (!response.ok) throw new Error(text("loadActivitiesFailed"));
      const payload = await response.json();
      state.activities = Array.isArray(payload.results) ? payload.results : [];
      state.activitiesLoaded = true;
    } catch (error) {
      state.activities = [];
      state.activitiesLoaded = true;
      setFeedback(error.message || text("loadActivitiesFailed"));
    }
  }

  async function syncDraftToServer() {
    if (!hasAuth() || !state.draft.start_date || !state.draft.end_date || state.syncing) return;
    state.syncing = true;
    try {
      await apiRequest("/funnel/draft/", {
        method: "PUT",
        body: JSON.stringify({
          start_date: state.draft.start_date,
          end_date: state.draft.end_date,
          adults: state.draft.adults,
          children: state.draft.children,
          budget_type: state.draft.budget_type,
          activities: state.draft.activities,
          language: getLang(),
        }),
      });
    } catch (_) {
      setFeedback(text("syncFailed"));
    } finally {
      state.syncing = false;
    }
  }

  function validateDraft() {
    if (!state.draft.start_date || !state.draft.end_date || !state.draft.activities.length) {
      throw new Error(text("validationMessage"));
    }
    if (state.draft.end_date < state.draft.start_date) {
      throw new Error(text("validationDateOrder"));
    }
    state.draft.adults = Math.max(1, Number(state.draft.adults || 1));
    state.draft.children = Math.max(0, Number(state.draft.children || 0));
    state.draft.selected_hotel_name = String(state.draft.selected_hotel_name || "").trim();
    state.draft.language = getLang();
    saveDraft();
  }

  async function requestDestinations() {
    try {
      validateDraft();
    } catch (error) {
      showLocalError(error);
      return;
    }

    state.loadingSuggestions = true;
    state.step = "destinations";
    setFeedback("");
    render();
    await syncDraftToServer();

    try {
      const payload = await apiRequest("/ai/suggest-cities/", {
        method: "POST",
        body: JSON.stringify({
          start_date: state.draft.start_date,
          end_date: state.draft.end_date,
          adults: state.draft.adults,
          children: state.draft.children,
          budget_type: state.draft.budget_type,
          activities: state.draft.activities,
          language: getLang(),
          family_mode: Number(state.draft.children) > 0,
        }),
      }, false);
      state.draft.suggestions = Array.isArray(payload.cities) ? payload.cities : [];
      state.draft.city = "";
      state.draft.city_description = "";
      clearAfterCity();
      saveDraft();
    } catch (error) {
      state.draft.suggestions = [];
      setFeedback(error.message || text("noCities"));
    } finally {
      state.loadingSuggestions = false;
      render();
    }
  }

  async function generatePlanOptions() {
    if (!state.draft.city || !state.draft.start_date || !state.draft.end_date) {
      setFeedback(text("validationMessage"));
      render();
      return;
    }
    state.generatingPlans = true;
    setFeedback("");
    render();
    try {
      const payload = await apiRequest("/plans/generate-options/", {
        method: "POST",
        body: JSON.stringify({
          city: state.draft.city,
          start_date: state.draft.start_date,
          end_date: state.draft.end_date,
          adults: state.draft.adults,
          children: state.draft.children,
          budget_type: state.draft.budget_type,
          activities: state.draft.activities,
          hotel_name: state.draft.selected_hotel_name || "",
          selected_tour_ids: [],
          language: getLang(),
          family_mode: Number(state.draft.children) > 0,
        }),
      });
      state.draft.plan_options = Array.isArray(payload.options) ? payload.options : [];
      state.step = "plans";
      saveDraft();
    } catch (error) {
      setFeedback(error.message || text("genericError"));
    } finally {
      state.generatingPlans = false;
      render();
    }
  }

  async function confirmPlan(planId) {
    if (!planId || state.confirmingPlanId) return;
    state.confirmingPlanId = planId;
    setFeedback("");
    render();
    try {
      await apiRequest("/plans/confirm/", {
        method: "POST",
        body: JSON.stringify({ plan_id: planId }),
      });
      state.draft.confirmed_plan_id = planId;
      state.step = "complete";
      saveDraft();
    } catch (error) {
      setFeedback(error.message || text("genericError"));
    } finally {
      state.confirmingPlanId = "";
      render();
    }
  }

  function redirectToAuth(path) {
    localStorage.setItem(RESUME_KEY, "1");
    saveDraft();
    const next = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    window.location.href = `${path}?next=${encodeURIComponent(next)}`;
  }

  function updateHeader() {
    const headerMap = {
      details: [text("stepDetails"), text("titleDetails"), text("subtitleDetails")],
      destinations: [text("stepDestinations"), text("titleDestinations"), text("subtitleDestinations")],
      account: [text("stepAccount"), text("titleAccount"), text("subtitleAccount")],
      plans: [text("stepPlans"), text("titlePlans"), text("subtitlePlans")],
      complete: [text("stepComplete"), text("titleComplete"), text("subtitleComplete")],
    };
    const [stepLabel, title, subtitle] = headerMap[state.step] || headerMap.details;
    modalStepLabel.textContent = stepLabel;
    modalTitle.textContent = title;
    modalSubtitle.textContent = subtitle;
  }

  function renderBudgetButton(value, label) {
    const active = state.draft.budget_type === value;
    return `<button type="button" data-plan-budget="${value}" class="border px-4 py-3 text-sm font-semibold transition ${
      active ? "border-slate-100 bg-slate-100 text-teal-700" : "border-slate-200/30 bg-white/5 text-slate-200 hover:bg-white/10"
    }">${label}</button>`;
  }

  function renderActivities() {
    if (!state.activities.length) {
      return `<p class="text-sm text-slate-200">${text("loadActivitiesFailed")}</p>`;
    }
    return state.activities.map((activity) => {
      const active = state.draft.activities.includes(activity.key);
      return `<button type="button" data-plan-activity="${escapeHtml(activity.key)}" class="flex min-h-[4.5rem] items-center gap-3 border px-4 py-3 text-left transition ${
        active ? "border-slate-100 bg-slate-100 text-teal-700" : "border-slate-200/30 bg-white/5 text-slate-100 hover:bg-white/10"
      }"><span class="inline-flex h-10 w-10 items-center justify-center border border-current/20 text-base">${active ? '<i class="fa-solid fa-check"></i>' : `<i class="fa-solid ${escapeHtml(activity.icon || "fa-star")}"></i>`}</span><span class="text-sm font-semibold">${escapeHtml(activity.name)}</span></button>`;
    }).join("");
  }

  function renderDetailsStep() {
    modalBody.innerHTML = `<div class="grid gap-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(18rem,0.85fr)]"><section class="space-y-8"><div><p class="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-slate-200">${text("datesLabel")}</p><div class="grid gap-4 md:grid-cols-2"><label class="space-y-2 text-sm font-medium text-slate-100"><span>${text("startDate")}</span><input id="plan-start-date" type="date" value="${escapeHtml(state.draft.start_date)}" class="w-full border border-slate-200/30 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-slate-100 placeholder:text-slate-300" /></label><label class="space-y-2 text-sm font-medium text-slate-100"><span>${text("endDate")}</span><input id="plan-end-date" type="date" value="${escapeHtml(state.draft.end_date)}" class="w-full border border-slate-200/30 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-slate-100 placeholder:text-slate-300" /></label></div></div><div class="grid gap-4 md:grid-cols-2"><label class="space-y-2 text-sm font-medium text-slate-100"><span>${text("adults")}</span><input id="plan-adults" type="number" min="1" value="${escapeHtml(state.draft.adults)}" class="w-full border border-slate-200/30 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-slate-100 placeholder:text-slate-300" /></label><label class="space-y-2 text-sm font-medium text-slate-100"><span>${text("children")}</span><input id="plan-children" type="number" min="0" value="${escapeHtml(state.draft.children)}" class="w-full border border-slate-200/30 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-slate-100 placeholder:text-slate-300" /></label></div><label class="space-y-2 text-sm font-medium text-slate-100"><span>${text("hotelNameLabel")}</span><input id="plan-hotel-name" type="text" maxlength="150" value="${escapeHtml(state.draft.selected_hotel_name)}" placeholder="${escapeHtml(text("hotelNamePlaceholder"))}" class="w-full border border-slate-200/30 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-slate-100 placeholder:text-slate-300" /><p class="text-xs leading-5 text-slate-300">${text("hotelNameHint")}</p></label><div><p class="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-slate-200">${text("budgetLabel")}</p><div class="grid gap-3 sm:grid-cols-3">${renderBudgetButton("cheap", text("budgetCheap"))}${renderBudgetButton("economy", text("budgetEconomy"))}${renderBudgetButton("luxury", text("budgetLuxury"))}</div></div></section><aside class="space-y-4"><div><p class="text-sm font-semibold uppercase tracking-[0.18em] text-slate-200">${text("activitiesLabel")}</p><p class="mt-2 text-sm text-slate-200">${text("activitiesHint")}</p></div><div class="grid gap-3 sm:grid-cols-2">${renderActivities()}</div><button id="plan-find-destinations" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-5 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200"><i class="fa-solid fa-stars"></i><span>${text("findDestinations")}</span></button></aside></div>`;

    const updateCore = (mutator) => {
      mutator();
      clearAfterPreferences();
      saveDraft();
    };

    document.getElementById("plan-start-date")?.addEventListener("input", (event) => updateCore(() => { state.draft.start_date = event.target.value; }));
    document.getElementById("plan-end-date")?.addEventListener("input", (event) => updateCore(() => { state.draft.end_date = event.target.value; }));
    document.getElementById("plan-adults")?.addEventListener("input", (event) => updateCore(() => { state.draft.adults = Math.max(1, Number(event.target.value || 1)); }));
    document.getElementById("plan-children")?.addEventListener("input", (event) => updateCore(() => { state.draft.children = Math.max(0, Number(event.target.value || 0)); }));
    document.getElementById("plan-hotel-name")?.addEventListener("input", (event) => {
      state.draft.selected_hotel_name = event.target.value;
      saveDraft();
    });
    modalBody.querySelectorAll("[data-plan-budget]").forEach((button) => {
      button.addEventListener("click", () => {
        updateCore(() => { state.draft.budget_type = button.dataset.planBudget; });
        render();
      });
    });
    modalBody.querySelectorAll("[data-plan-activity]").forEach((button) => {
      button.addEventListener("click", () => {
        updateCore(() => {
          const key = button.dataset.planActivity;
          const nextActivities = new Set(state.draft.activities);
          if (nextActivities.has(key)) nextActivities.delete(key); else nextActivities.add(key);
          state.draft.activities = Array.from(nextActivities);
        });
        render();
      });
    });
    document.getElementById("plan-find-destinations")?.addEventListener("click", requestDestinations);
  }

  function renderDestinationCards() {
    if (state.loadingSuggestions) {
      return `<div class="flex min-h-[18rem] items-center justify-center border border-slate-200/20 bg-white/5 px-6 py-10 text-center text-slate-100"><div><i class="fa-solid fa-compass animate-pulse text-3xl"></i><p class="mt-4 text-base">${text("loadingCities")}</p></div></div>`;
    }
    if (!state.draft.suggestions.length) {
      return `<div class="space-y-5 border border-slate-200/20 bg-white/5 px-6 py-10 text-center text-slate-100"><p>${text("noCities")}</p><button id="plan-back-details-empty" type="button" class="inline-flex items-center justify-center border border-slate-200/30 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:bg-white/10">${text("back")}</button></div>`;
    }
    return `<div class="grid gap-4 lg:grid-cols-3">${state.draft.suggestions.map((item, index) => `<article class="flex h-full flex-col border border-slate-200/20 bg-white/5 p-5 text-slate-100"><div class="flex items-center justify-between gap-3"><h3 class="font-display text-2xl text-slate-100">${escapeHtml(item.city)}</h3><span class="border border-slate-200/20 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-200">AI</span></div><p class="mt-4 flex-1 text-sm leading-6 text-slate-200">${escapeHtml(item.description || "")}</p><button type="button" data-plan-city-index="${index}" class="mt-6 inline-flex items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-4 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200"><i class="fa-solid fa-location-dot"></i><span>${text("selectDestination")}</span></button></article>`).join("")}</div>`;
  }

  function renderDestinationsStep() {
    modalBody.innerHTML = `<div class="space-y-6"><div class="flex items-center justify-between gap-4"><p class="max-w-2xl text-sm text-slate-200">${text("subtitleDestinations")}</p><button id="plan-back-details" type="button" class="inline-flex items-center justify-center gap-2 border border-slate-200/30 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:bg-white/10"><i class="fa-solid fa-arrow-left"></i><span>${text("back")}</span></button></div>${renderDestinationCards()}</div>`;
    document.getElementById("plan-back-details")?.addEventListener("click", () => { state.step = "details"; render(); });
    document.getElementById("plan-back-details-empty")?.addEventListener("click", () => { state.step = "details"; render(); });
    modalBody.querySelectorAll("[data-plan-city-index]").forEach((button) => {
      button.addEventListener("click", async () => {
        const item = state.draft.suggestions[Number(button.dataset.planCityIndex)];
        if (!item) return;
        state.draft.city = item.city;
        state.draft.city_description = item.description || "";
        clearAfterCity();
        saveDraft();
        if (hasAuth()) {
          await syncDraftToServer();
          state.step = "plans";
          await generatePlanOptions();
        } else {
          state.step = "account";
          render();
        }
      });
    });
  }

  function renderAccountStep() {
    modalBody.innerHTML = `<div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]"><div class="border border-slate-200/20 bg-white/5 p-6 text-slate-100"><p class="text-sm uppercase tracking-[0.18em] text-slate-200">${text("selectedDestination")}</p><h3 class="mt-3 font-display text-3xl text-slate-100">${escapeHtml(state.draft.city)}</h3><p class="mt-4 text-sm leading-6 text-slate-200">${escapeHtml(state.draft.city_description)}</p><p class="mt-6 text-sm text-slate-200">${text("subtitleAccount")}</p></div><div class="space-y-3"><button id="plan-signin" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-5 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200">${text("signInToContinue")}</button><button id="plan-signup" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-200/30 bg-white/5 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10">${text("signUpToContinue")}</button><button id="plan-back-destinations" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-200/30 bg-white/5 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10">${text("back")}</button></div></div>`;
    document.getElementById("plan-signin")?.addEventListener("click", () => redirectToAuth("/login/"));
    document.getElementById("plan-signup")?.addEventListener("click", () => redirectToAuth("/register/"));
    document.getElementById("plan-back-destinations")?.addEventListener("click", () => { state.step = "destinations"; render(); });
  }

  function renderPlanOption(option) {
    const confirming = state.confirmingPlanId === option.plan_id;
    return `<article class="border border-slate-200/20 bg-white/5 p-5 text-slate-100"><div class="flex flex-col gap-4 border-b border-slate-200/10 pb-5 lg:flex-row lg:items-start lg:justify-between"><div><h3 class="font-display text-3xl text-slate-100">${escapeHtml(option.title || "Plan")}</h3><p class="mt-3 line-clamp-3 text-sm leading-6 text-slate-200">${escapeHtml(option.gemini_recommendation || option.summary || "")}</p></div><div class="min-w-[12rem] border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("estimatedTotal")}</p><p class="mt-2 text-base font-semibold text-slate-100">${escapeHtml(option.estimated_total || "-")} ${escapeHtml(option.currency || "TRY")}</p></div></div><div class="mt-5 space-y-4">${(option.days || []).map((day) => `<section class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("dayLabel")} ${escapeHtml(day.day)}</p><div class="mt-4 space-y-3">${(day.timeline || []).map((item) => `<div class="grid gap-2 border border-slate-200/5 bg-white/[0.02] p-3 md:grid-cols-[5rem_minmax(0,1fr)] md:items-start"><span class="text-sm font-semibold text-lagoon-300">${escapeHtml(item.time)}</span><div><p class="text-sm font-semibold text-slate-100">${escapeHtml(item.title)}</p>${item.notes ? `<p class="mt-1 line-clamp-2 text-sm text-slate-200">${escapeHtml(item.notes)}</p>` : ""}</div></div>`).join("")}</div></section>`).join("")}</div><button type="button" data-plan-confirm="${escapeHtml(option.plan_id)}" class="mt-6 inline-flex items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-5 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200 ${confirming ? "opacity-60" : ""}" ${confirming ? "disabled" : ""}><i class="fa-solid fa-check"></i><span>${confirming ? text("loadingPlan") : text("confirmPlan")}</span></button></article>`;
  }

  function renderPlansStep() {
    modalBody.innerHTML = `<div class="space-y-6"><div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_18rem]"><div class="border border-slate-200/20 bg-white/5 p-5 text-slate-100"><p class="text-xs uppercase tracking-[0.18em] text-slate-200">${text("selectedDestination")}</p><h3 class="mt-2 font-display text-3xl text-slate-100">${escapeHtml(state.draft.city)}</h3><p class="mt-2 text-sm text-slate-200">${escapeHtml(state.draft.start_date)} — ${escapeHtml(state.draft.end_date)}</p>${state.draft.selected_hotel_name ? `<p class="mt-2 text-sm text-slate-200">${escapeHtml(state.draft.selected_hotel_name)}</p>` : ""}</div><button id="plan-back-destinations-from-plans" type="button" class="inline-flex h-fit items-center justify-center gap-2 border border-slate-200/30 px-4 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10"><i class="fa-solid fa-arrow-left"></i><span>${text("back")}</span></button></div>${state.generatingPlans ? `<div class="flex min-h-[16rem] items-center justify-center border border-slate-200/20 bg-white/5 px-6 py-10 text-center text-slate-100"><div><i class="fa-solid fa-route animate-pulse text-3xl"></i><p class="mt-4 text-base">${text("generatingPlans")}</p></div></div>` : ""}${!state.generatingPlans && state.draft.plan_options.length ? `<div class="grid gap-6 xl:grid-cols-2">${state.draft.plan_options.map(renderPlanOption).join("")}</div>` : ""}${!state.generatingPlans && !state.draft.plan_options.length ? `<div class="space-y-5 border border-slate-200/20 bg-white/5 px-6 py-10 text-center text-slate-100"><p>${text("noActivePlan")}</p><button id="plan-retry-generate" type="button" class="inline-flex items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-4 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200">${text("retryGenerate")}</button></div>` : ""}</div>`;
    document.getElementById("plan-back-destinations-from-plans")?.addEventListener("click", () => { state.step = "destinations"; render(); });
    document.getElementById("plan-retry-generate")?.addEventListener("click", generatePlanOptions);
    modalBody.querySelectorAll("[data-plan-confirm]").forEach((button) => {
      button.addEventListener("click", () => confirmPlan(button.dataset.planConfirm));
    });
  }

  function selectedPlan() {
    return state.draft.plan_options.find((item) => item.plan_id === state.draft.confirmed_plan_id) || state.draft.plan_options[0] || null;
  }

  function renderCompleteStep() {
    const option = selectedPlan();
    modalBody.innerHTML = `<div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]"><div class="space-y-5 border border-slate-200/20 bg-white/5 p-6 text-slate-100"><div><p class="text-sm uppercase tracking-[0.18em] text-slate-200">${text("selectedDestination")}</p><h3 class="mt-2 font-display text-3xl text-slate-100">${escapeHtml(state.draft.city)}</h3>${state.draft.selected_hotel_name ? `<p class="mt-3 text-sm text-slate-200">${escapeHtml(state.draft.selected_hotel_name)}</p>` : ""}</div><div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><div class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("startDate")}</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(state.draft.start_date)}</p></div><div class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("endDate")}</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(state.draft.end_date)}</p></div><div class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("guestsLabel")}</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(guestSummary())}</p></div><div class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("planIdLabel")}</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(state.draft.confirmed_plan_id)}</p></div></div>${option ? `<div class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("optionLabel")}</p><p class="mt-2 text-base font-semibold text-slate-100">${escapeHtml(option.title || "Plan")}</p><p class="mt-2 line-clamp-3 text-sm text-slate-200">${escapeHtml(option.gemini_recommendation || option.summary || "")}</p><a href="/account/" class="mt-4 inline-flex items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-4 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200"><i class="fa-solid fa-arrow-up-right-from-square"></i><span>${text("viewDetails")}</span></a><p class="mt-3 text-xs uppercase tracking-[0.16em] text-slate-300">${text("viewDetailsHint")}</p></div>` : ""}</div><div class="space-y-3"><a href="/account/" class="inline-flex w-full items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-5 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200">${text("goToAccount")}</a><button id="plan-create-another" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-200/30 bg-white/5 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10">${text("createAnotherPlan")}</button><button id="plan-complete-close" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-200/30 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10">${text("close")}</button></div></div>`;
    document.getElementById("plan-complete-close")?.addEventListener("click", closeModal);
    document.getElementById("plan-create-another")?.addEventListener("click", () => {
      state.draft = normalizeDraft({ language: getLang() });
      saveDraft();
      state.step = "details";
      render();
    });
  }

  function render() {
    updateHeader();
    setFeedback(state.feedback, state.feedbackType);
    if (state.step === "destinations") return renderDestinationsStep();
    if (state.step === "account") return renderAccountStep();
    if (state.step === "plans") return renderPlansStep();
    if (state.step === "complete") return renderCompleteStep();
    return renderDetailsStep();
  }

  async function prepareStep() {
    await ensureActivitiesLoaded();
    if (state.step === "plans" && !state.draft.plan_options.length && hasAuth() && !state.generatingPlans) {
      await generatePlanOptions();
    }
  }

  async function openModal(nextStep) {
    resetMobileMenu();
    await loadServerDraftIfNeeded();
    state.step = nextStep || computeStep();
    await prepareStep();
    render();
    modal.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  }

  closeBtn?.addEventListener("click", closeModal);
  modal.addEventListener("click", (event) => {
    if (event.target === modal) closeModal();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.classList.contains("hidden")) closeModal();
  });
  openBtn?.addEventListener("click", () => openModal());
  openMobileBtn?.addEventListener("click", () => openModal());
  document.addEventListener("turquaway:languagechange", async () => {
    state.draft.language = getLang();
    saveDraft();
    state.activitiesLoaded = false;
    await ensureActivitiesLoaded();
    if (!modal.classList.contains("hidden")) render();
  });
  document.addEventListener("DOMContentLoaded", async () => {
    if (localStorage.getItem(RESUME_KEY) === "1" && hasAuth() && hasMeaningfulDraft()) {
      localStorage.removeItem(RESUME_KEY);
      setFeedback(text("draftRestored"), "success");
      await openModal();
    }
  });
})();
