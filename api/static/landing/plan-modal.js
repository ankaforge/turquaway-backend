(() => {
  const BASE_STRINGS = {
    stepDetails: "Trip Details",
    stepDestinations: "Suggested Destinations",
    stepAccount: "Account Required",
    stepHotels: "Hotel Reservation",
    stepTours: "Tour Selection",
    stepPlans: "Plan Options",
    stepComplete: "Plan Confirmed",
    titleDetails: "Build your travel plan",
    subtitleDetails: "Choose dates, guest count, budget, and activities. Your draft stays in browser storage so the flow can continue after authentication.",
    titleDestinations: "Pick your destination",
    subtitleDestinations: "These cities are suggested by AI according to the details you entered.",
    titleAccount: "Sign in to continue",
    subtitleAccount: "Your draft is safe. Authenticate now and continue from the selected destination.",
    titleHotels: "Choose and reserve your hotel",
    subtitleHotels: "For now hotel reservation uses the current backend model. Later this step can switch to Agoda Search and Book APIs without changing the draft flow.",
    titleTours: "Pick your tours",
    subtitleTours: "Select the tours that should be woven into your final itinerary. They will be reserved when you confirm the plan.",
    titlePlans: "Review generated plan options",
    subtitlePlans: "Compare the two AI-generated itineraries and confirm the one that fits best.",
    titleComplete: "Your plan is active",
    subtitleComplete: "The selected hotel, tours, and confirmed itinerary are now ready. You can review everything from your account page.",
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
    loadingHotels: "Looking up hotel options in this city...",
    noHotels: "No hotels matched your criteria right now.",
    reserveHotel: "Reserve this hotel",
    reservedHotel: "Hotel reserved",
    loadingTours: "Finding tours near your selected hotel...",
    noTours: "No tours were returned for this destination. You can still generate a plan without tours.",
    generatePlans: "Generate plan options",
    selectedHotel: "Selected hotel",
    selectedTours: "Selected tours",
    optionalToursHint: "Tour selection is optional. If you continue without tours, the itinerary will be generated around the city and hotel only.",
    reservingHotel: "Reserving hotel...",
    generatingPlans: "Generating plan options...",
    confirmPlan: "Confirm this plan",
    estimatedTotal: "Estimated total",
    loadingPlan: "Preparing your final itinerary...",
    goToAccount: "Go to account",
    createAnotherPlan: "Create another plan",
    hotelNightlyPrice: "Nightly price per person",
    hotelRating: "Rating",
    sponsoredBadge: "AI pick",
    continueWithoutTours: "Continue without tours",
    noActivePlan: "No confirmed plan is stored yet.",
    guestProfileMissing: "Profile details could not be resolved for hotel reservation.",
    serverDraftLoaded: "Your account draft was loaded.",
    genericError: "Something went wrong. Please try again.",
    hotelReservedBody: "Your hotel reservation was created in the current backend flow. Agoda integration can replace this later.",
  };

  const STRINGS = {
    en: BASE_STRINGS,
    tr: {
      ...BASE_STRINGS,
      stepDetails: "Seyahat Detayları",
      stepDestinations: "Önerilen Destinasyonlar",
      stepAccount: "Hesap Gerekli",
      stepHotels: "Otel Rezervasyonu",
      stepTours: "Tur Seçimi",
      stepPlans: "Plan Seçenekleri",
      stepComplete: "Plan Onaylandı",
      titleDetails: "Seyahat planını oluştur",
      subtitleDetails: "Tarihleri, misafir sayısını, bütçeyi ve aktiviteleri seç. Taslak tarayıcı hafızasında saklanır; girişten sonra aynı yerden devam edilir.",
      titleDestinations: "Destinasyonunu seç",
      subtitleDestinations: "Bu şehirler girdiğin tercihlere göre yapay zeka tarafından önerildi.",
      titleAccount: "Devam etmek için giriş yap",
      subtitleAccount: "Taslağın güvende. Şimdi giriş yap veya üye ol; seçtiğin destinasyondan devam et.",
      titleHotels: "Otelini seç ve rezerve et",
      subtitleHotels: "Şimdilik otel rezervasyonu mevcut backend modelini kullanıyor. Daha sonra bu adım Agoda Search ve Book API ile değiştirilebilir.",
      titleTours: "Turlarını seç",
      subtitleTours: "Son planına işlenmesini istediğin turları seç. Bu turlar planı onayladığında rezerve edilecek.",
      titlePlans: "Üretilen plan seçeneklerini incele",
      subtitlePlans: "İki yapay zeka planını karşılaştır ve sana en uygun olanı onayla.",
      titleComplete: "Planın aktif",
      subtitleComplete: "Seçilen otel, turlar ve onaylanan rota hazır. Her şeyi hesap sayfandan takip edebilirsin.",
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
      loadingHotels: "Bu şehirdeki oteller listeleniyor...",
      noHotels: "Şu anda kriterlerine uygun otel bulunamadı.",
      reserveHotel: "Bu oteli rezerve et",
      reservedHotel: "Otel rezerve edildi",
      loadingTours: "Seçtiğin otele yakın turlar aranıyor...",
      noTours: "Bu destinasyon için tur dönmedi. Tursuz şekilde de plan üretebilirsin.",
      generatePlans: "Plan seçenekleri oluştur",
      selectedHotel: "Seçilen otel",
      selectedTours: "Seçilen turlar",
      optionalToursHint: "Tur seçimi opsiyoneldir. Tur seçmeden devam edersen plan sadece şehir ve otel etrafında üretilir.",
      reservingHotel: "Otel rezerve ediliyor...",
      generatingPlans: "Plan seçenekleri üretiliyor...",
      confirmPlan: "Bu planı onayla",
      estimatedTotal: "Tahmini toplam",
      loadingPlan: "Final rota hazırlanıyor...",
      goToAccount: "Hesaba git",
      createAnotherPlan: "Yeni plan oluştur",
      hotelNightlyPrice: "Kişi başı gecelik fiyat",
      hotelRating: "Puan",
      sponsoredBadge: "AI önerisi",
      continueWithoutTours: "Tursuz devam et",
      noActivePlan: "Henüz onaylanmış plan yok.",
      guestProfileMissing: "Otel rezervasyonu için profil bilgileri çözümlenemedi.",
      serverDraftLoaded: "Hesabındaki taslak yüklendi.",
      genericError: "Bir sorun oluştu. Lütfen tekrar dene.",
      hotelReservedBody: "Otel rezervasyonun mevcut backend akışında oluşturuldu. Agoda entegrasyonu geldiğinde bu adım değiştirilebilir.",
    },
    ru: { ...BASE_STRINGS },
    ar: { ...BASE_STRINGS },
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
    hotel_results: [],
    selected_hotel_id: "",
    selected_hotel_name: "",
    hotel_reservation_id: "",
    hotel_reservation_status: "",
    tour_results: [],
    selected_tour_ids: [],
    plan_options: [],
    confirmed_plan_id: "",
    tour_empty_state: false,
    tour_fallback: null,
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
    loadingHotels: false,
    reservingHotelId: "",
    loadingTours: false,
    generatingPlans: false,
    confirmingPlanId: "",
    syncing: false,
    feedback: "",
    feedbackType: "error",
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
      hotel_results: Array.isArray(raw?.hotel_results) ? raw.hotel_results : [],
      tour_results: Array.isArray(raw?.tour_results) ? raw.tour_results : [],
      selected_tour_ids: Array.isArray(raw?.selected_tour_ids) ? raw.selected_tour_ids : [],
      plan_options: Array.isArray(raw?.plan_options) ? raw.plan_options : [],
      language: raw?.language || getLang(),
    };
  }

  function saveDraft() {
    state.draft.language = getLang();
    localStorage.setItem(DRAFT_KEY, JSON.stringify(state.draft));
  }

  function clearAfterPreferences() {
    state.draft.suggestions = [];
    state.draft.city = "";
    state.draft.city_description = "";
    state.draft.hotel_results = [];
    state.draft.selected_hotel_id = "";
    state.draft.selected_hotel_name = "";
    state.draft.hotel_reservation_id = "";
    state.draft.hotel_reservation_status = "";
    state.draft.tour_results = [];
    state.draft.selected_tour_ids = [];
    state.draft.plan_options = [];
    state.draft.confirmed_plan_id = "";
    state.draft.tour_empty_state = false;
    state.draft.tour_fallback = null;
  }

  function clearAfterCity() {
    state.draft.hotel_results = [];
    state.draft.selected_hotel_id = "";
    state.draft.selected_hotel_name = "";
    state.draft.hotel_reservation_id = "";
    state.draft.hotel_reservation_status = "";
    state.draft.tour_results = [];
    state.draft.selected_tour_ids = [];
    state.draft.plan_options = [];
    state.draft.confirmed_plan_id = "";
    state.draft.tour_empty_state = false;
    state.draft.tour_fallback = null;
  }

  function clearAfterHotel() {
    state.draft.tour_results = [];
    state.draft.selected_tour_ids = [];
    state.draft.plan_options = [];
    state.draft.confirmedPlanId = "";
    state.draft.confirmed_plan_id = "";
    state.draft.tour_empty_state = false;
    state.draft.tour_fallback = null;
  }

  function hasAuth() {
    return Boolean(localStorage.getItem("tw_access"));
  }

  function authHeaders() {
    const token = localStorage.getItem("tw_access");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  function hasMeaningfulDraft() {
    return Boolean(
      state.draft.start_date ||
      state.draft.end_date ||
      state.draft.activities.length ||
      state.draft.city ||
      state.draft.hotel_reservation_id ||
      state.draft.plan_options.length ||
      state.draft.confirmed_plan_id
    );
  }

  function computeStep() {
    if (state.draft.confirmed_plan_id) return "complete";
    if (state.draft.plan_options.length) return "plans";
    if (state.draft.hotel_reservation_id) return "tours";
    if (state.draft.city) return hasAuth() ? "hotels" : "account";
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
        redirectToAuth("/login/");
      }
      const error = new Error(payload.detail || text("genericError"));
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return payload;
  }

  function readStoredUser() {
    try {
      return JSON.parse(localStorage.getItem("tw_user") || "null");
    } catch (_) {
      return null;
    }
  }

  async function ensureCurrentUser() {
    const user = readStoredUser();
    if (user?.full_name && user?.email) return user;
    const payload = await apiRequest("/me/", { method: "GET" });
    localStorage.setItem("tw_user", JSON.stringify(payload));
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

  async function loadHotels(force = false) {
    if (!hasAuth()) {
      state.step = "account";
      render();
      return;
    }
    if (!state.draft.city || state.loadingHotels) return;
    if (!force && state.draft.hotel_results.length) return;

    state.loadingHotels = true;
    render();
    try {
      const payload = await apiRequest("/hotels/search/", {
        method: "POST",
        body: JSON.stringify({
          city: state.draft.city,
          start_date: state.draft.start_date,
          end_date: state.draft.end_date,
          adults: state.draft.adults,
          children: state.draft.children,
          budget_type: state.draft.budget_type,
          activities: state.draft.activities,
          language: getLang(),
          sort: "price_asc",
        }),
      });
      state.draft.hotel_results = Array.isArray(payload.hotels) ? payload.hotels : [];
      saveDraft();
    } catch (error) {
      setFeedback(error.message || text("noHotels"));
    } finally {
      state.loadingHotels = false;
      render();
    }
  }

  async function reserveHotel(hotelId) {
    if (!hotelId || state.reservingHotelId) return;
    state.reservingHotelId = hotelId;
    setFeedback("");
    render();
    try {
      const user = await ensureCurrentUser();
      if (!user?.full_name || !user?.email) {
        throw new Error(text("guestProfileMissing"));
      }
      const payload = await apiRequest("/hotel-reservations/", {
        method: "POST",
        body: JSON.stringify({
          hotel_id: hotelId,
          start_date: state.draft.start_date,
          end_date: state.draft.end_date,
          adults: state.draft.adults,
          children: state.draft.children,
          guest_contact: {
            full_name: user.full_name,
            email: user.email,
            phone: user.phone,
            country: user.country,
          },
        }),
      });
      const hotel = state.draft.hotel_results.find((item) => item.id === hotelId);
      state.draft.selected_hotel_id = hotelId;
      state.draft.selected_hotel_name = hotel?.name || "";
      state.draft.hotel_reservation_id = payload.reservation_id || "";
      state.draft.hotel_reservation_status = payload.status || "";
      clearAfterHotel();
      saveDraft();
      setFeedback(text("hotelReservedBody"), "success");
      state.step = "tours";
      await loadTours(true);
    } catch (error) {
      setFeedback(error.message || text("genericError"));
    } finally {
      state.reservingHotelId = "";
      render();
    }
  }

  async function loadTours(force = false) {
    if (!hasAuth()) {
      state.step = "account";
      render();
      return;
    }
    if (!state.draft.city || !state.draft.selected_hotel_id || state.loadingTours) return;
    if (!force && state.draft.tour_results.length) return;

    state.loadingTours = true;
    render();
    try {
      const payload = await apiRequest("/tours/search/", {
        method: "POST",
        body: JSON.stringify({
          hotel_id: state.draft.selected_hotel_id,
          city: state.draft.city,
          adults: state.draft.adults,
          children: state.draft.children,
          budget_type: state.draft.budget_type,
          activities: state.draft.activities,
          radius_km: 30,
          language: getLang(),
        }),
      });
      state.draft.tour_results = Array.isArray(payload.tours) ? payload.tours : [];
      state.draft.tour_empty_state = Boolean(payload.empty_state);
      state.draft.tour_fallback = payload.diy_fallback || null;
      saveDraft();
    } catch (error) {
      state.draft.tour_results = [];
      state.draft.tour_empty_state = true;
      state.draft.tour_fallback = null;
      setFeedback(error.message || text("noTours"));
    } finally {
      state.loadingTours = false;
      render();
    }
  }

  async function generatePlanOptions() {
    if (!state.draft.hotel_reservation_id) {
      setFeedback(text("genericError"));
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
          hotel_reservation_id: state.draft.hotel_reservation_id,
          selected_tour_ids: state.draft.selected_tour_ids,
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
      hotels: [text("stepHotels"), text("titleHotels"), text("subtitleHotels")],
      tours: [text("stepTours"), text("titleTours"), text("subtitleTours")],
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
      }"><span class="inline-flex h-10 w-10 items-center justify-center border border-current/20 text-base"><i class="fa-solid ${escapeHtml(activity.icon || "fa-star")}"></i></span><span class="text-sm font-semibold">${escapeHtml(activity.name)}</span></button>`;
    }).join("");
  }

  function renderDetailsStep() {
    modalBody.innerHTML = `<div class="grid gap-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(18rem,0.85fr)]"><section class="space-y-8"><div><p class="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-slate-200">${text("datesLabel")}</p><div class="grid gap-4 md:grid-cols-2"><label class="space-y-2 text-sm font-medium text-slate-100"><span>${text("startDate")}</span><input id="plan-start-date" type="date" value="${escapeHtml(state.draft.start_date)}" class="w-full border border-slate-200/30 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-slate-100 placeholder:text-slate-300" /></label><label class="space-y-2 text-sm font-medium text-slate-100"><span>${text("endDate")}</span><input id="plan-end-date" type="date" value="${escapeHtml(state.draft.end_date)}" class="w-full border border-slate-200/30 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-slate-100 placeholder:text-slate-300" /></label></div></div><div class="grid gap-4 md:grid-cols-2"><label class="space-y-2 text-sm font-medium text-slate-100"><span>${text("adults")}</span><input id="plan-adults" type="number" min="1" value="${escapeHtml(state.draft.adults)}" class="w-full border border-slate-200/30 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-slate-100 placeholder:text-slate-300" /></label><label class="space-y-2 text-sm font-medium text-slate-100"><span>${text("children")}</span><input id="plan-children" type="number" min="0" value="${escapeHtml(state.draft.children)}" class="w-full border border-slate-200/30 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-slate-100 placeholder:text-slate-300" /></label></div><div><p class="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-slate-200">${text("budgetLabel")}</p><div class="grid gap-3 sm:grid-cols-3">${renderBudgetButton("cheap", text("budgetCheap"))}${renderBudgetButton("economy", text("budgetEconomy"))}${renderBudgetButton("luxury", text("budgetLuxury"))}</div></div></section><aside class="space-y-4"><div><p class="text-sm font-semibold uppercase tracking-[0.18em] text-slate-200">${text("activitiesLabel")}</p><p class="mt-2 text-sm text-slate-200">${text("activitiesHint")}</p></div><div class="grid gap-3 sm:grid-cols-2">${renderActivities()}</div><button id="plan-find-destinations" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-5 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200"><i class="fa-solid fa-stars"></i><span>${text("findDestinations")}</span></button></aside></div>`;

    const updateCore = (mutator) => {
      mutator();
      clearAfterPreferences();
      saveDraft();
    };

    document.getElementById("plan-start-date")?.addEventListener("input", (event) => updateCore(() => { state.draft.start_date = event.target.value; }));
    document.getElementById("plan-end-date")?.addEventListener("input", (event) => updateCore(() => { state.draft.end_date = event.target.value; }));
    document.getElementById("plan-adults")?.addEventListener("input", (event) => updateCore(() => { state.draft.adults = Math.max(1, Number(event.target.value || 1)); }));
    document.getElementById("plan-children")?.addEventListener("input", (event) => updateCore(() => { state.draft.children = Math.max(0, Number(event.target.value || 0)); }));
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
          state.step = "hotels";
          await loadHotels(true);
        } else {
          state.step = "account";
          render();
        }
      });
    });
  }

  function renderAccountStep() {
    modalBody.innerHTML = `<div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]"><div class="border border-slate-200/20 bg-white/5 p-6 text-slate-100"><p class="text-sm uppercase tracking-[0.18em] text-slate-200">${text("selectedDestination")}</p><h3 class="mt-3 font-display text-3xl text-slate-100">${escapeHtml(state.draft.city)}</h3><p class="mt-4 text-sm leading-6 text-slate-200">${escapeHtml(state.draft.city_description)}</p><p class="mt-6 text-sm text-slate-200">${text("subtitleAccount")}</p></div><div class="space-y-3"><button id="plan-signin" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-5 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200">${text("signInToContinue")}</button><button id="plan-signup" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-200/30 bg-white/5 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10">${text("signUpToContinue")}</button><button id="plan-back-destinations" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-200/30 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10">${text("back")}</button></div></div>`;
    document.getElementById("plan-signin")?.addEventListener("click", () => redirectToAuth("/login/"));
    document.getElementById("plan-signup")?.addEventListener("click", () => redirectToAuth("/register/"));
    document.getElementById("plan-back-destinations")?.addEventListener("click", () => { state.step = "destinations"; render(); });
  }

  function hotelCard(hotel) {
    const reserving = state.reservingHotelId === hotel.id;
    return `<article class="flex h-full flex-col border border-slate-200/20 bg-white/5 text-slate-100"><div class="aspect-[16/10] overflow-hidden border-b border-slate-200/10 bg-slate-900/40">${hotel.image ? `<img src="${escapeHtml(hotel.image)}" alt="${escapeHtml(hotel.name)}" class="h-full w-full object-cover" />` : `<div class="flex h-full items-center justify-center text-slate-300"><i class="fa-solid fa-hotel text-3xl"></i></div>`}</div><div class="flex flex-1 flex-col p-5"><div class="flex items-start justify-between gap-3"><div><h3 class="font-display text-2xl text-slate-100">${escapeHtml(hotel.name)}</h3><p class="mt-2 text-sm text-slate-200">${escapeHtml(hotel.city || state.draft.city)}</p></div>${hotel.sponsored ? `<span class="border border-slate-200/20 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-200">${text("sponsoredBadge")}</span>` : ""}</div><div class="mt-5 grid gap-3 sm:grid-cols-2"><div class="border border-slate-200/10 p-3"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("hotelNightlyPrice")}</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(hotel.nightly_price_per_person)} ${escapeHtml(hotel.currency || "TRY")}</p></div><div class="border border-slate-200/10 p-3"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("hotelRating")}</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(hotel.rating || 0)}</p></div></div><button type="button" data-plan-reserve-hotel="${escapeHtml(hotel.id)}" class="mt-6 inline-flex items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-4 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200 ${reserving ? "opacity-60" : ""}" ${reserving ? "disabled" : ""}><i class="fa-solid fa-building-circle-check"></i><span>${reserving ? text("reservingHotel") : text("reserveHotel")}</span></button></div></article>`;
  }

  function renderHotelsStep() {
    modalBody.innerHTML = `<div class="space-y-6"><div class="flex flex-col gap-4 border border-slate-200/20 bg-white/5 p-5 text-slate-100 lg:flex-row lg:items-center lg:justify-between"><div><p class="text-xs uppercase tracking-[0.18em] text-slate-200">${text("selectedDestination")}</p><h3 class="mt-2 font-display text-3xl text-slate-100">${escapeHtml(state.draft.city)}</h3><p class="mt-2 text-sm text-slate-200">${escapeHtml(state.draft.city_description)}</p></div><button id="plan-back-destinations-from-hotels" type="button" class="inline-flex items-center justify-center gap-2 border border-slate-200/30 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:bg-white/10"><i class="fa-solid fa-arrow-left"></i><span>${text("back")}</span></button></div>${state.loadingHotels ? `<div class="flex min-h-[16rem] items-center justify-center border border-slate-200/20 bg-white/5 px-6 py-10 text-center text-slate-100"><div><i class="fa-solid fa-hotel animate-pulse text-3xl"></i><p class="mt-4 text-base">${text("loadingHotels")}</p></div></div>` : ""}${!state.loadingHotels && !state.draft.hotel_results.length ? `<div class="border border-slate-200/20 bg-white/5 px-6 py-10 text-center text-slate-100"><p>${text("noHotels")}</p></div>` : ""}${!state.loadingHotels && state.draft.hotel_results.length ? `<div class="grid gap-4 xl:grid-cols-2">${state.draft.hotel_results.map(hotelCard).join("")}</div>` : ""}</div>`;
    document.getElementById("plan-back-destinations-from-hotels")?.addEventListener("click", () => { state.step = "destinations"; render(); });
    modalBody.querySelectorAll("[data-plan-reserve-hotel]").forEach((button) => {
      button.addEventListener("click", () => reserveHotel(button.dataset.planReserveHotel));
    });
  }

  function renderTourCard(tour) {
    const active = state.draft.selected_tour_ids.includes(tour.id);
    const firstSessions = Array.isArray(tour.available_sessions) ? tour.available_sessions.slice(0, 3) : [];
    return `<article class="flex h-full flex-col border border-slate-200/20 bg-white/5 p-5 text-slate-100"><div class="flex items-start justify-between gap-3"><div><h3 class="font-display text-2xl text-slate-100">${escapeHtml(tour.title)}</h3><p class="mt-3 text-sm leading-6 text-slate-200">${escapeHtml(tour.description || "")}</p></div><button type="button" data-plan-toggle-tour="${escapeHtml(tour.id)}" class="inline-flex items-center justify-center border px-3 py-2 text-sm font-semibold transition ${active ? "border-slate-100 bg-slate-100 text-teal-700" : "border-slate-200/30 text-slate-100 hover:bg-white/10"}">${active ? "Selected" : "Select"}</button></div><div class="mt-5 grid gap-3 sm:grid-cols-2"><div class="border border-slate-200/10 p-3"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">Adult</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(tour.price_adult)} ${escapeHtml(tour.currency || "TRY")}</p></div><div class="border border-slate-200/10 p-3"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">Child</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(tour.price_child)} ${escapeHtml(tour.currency || "TRY")}</p></div></div><div class="mt-5 space-y-2 text-sm text-slate-200">${firstSessions.length ? firstSessions.map((session) => `<div class="border border-slate-200/10 bg-white/[0.02] px-3 py-2"><p class="font-semibold text-slate-100">${escapeHtml(session.date)}</p><p class="mt-1">${escapeHtml(session.start_time)} - ${escapeHtml(session.end_time)}</p><p class="mt-1 text-slate-200">Available: ${escapeHtml(session.available_spots)}</p></div>`).join("") : `<p>${text("noTours")}</p>`}</div></article>`;
  }

  function renderToursStep() {
    modalBody.innerHTML = `<div class="space-y-6"><div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_18rem]"><div class="border border-slate-200/20 bg-white/5 p-5 text-slate-100"><p class="text-xs uppercase tracking-[0.18em] text-slate-200">${text("selectedHotel")}</p><h3 class="mt-2 font-display text-3xl text-slate-100">${escapeHtml(state.draft.selected_hotel_name)}</h3><p class="mt-2 text-sm text-slate-200">${escapeHtml(state.draft.city)}</p><p class="mt-4 text-sm text-slate-200">${text("optionalToursHint")}</p></div><div class="space-y-3"><button id="plan-back-hotels" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-200/30 px-4 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10"><i class="fa-solid fa-arrow-left"></i><span>${text("back")}</span></button><button id="plan-generate-from-tours" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-4 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200 ${state.generatingPlans ? "opacity-60" : ""}" ${state.generatingPlans ? "disabled" : ""}><i class="fa-solid fa-route"></i><span>${state.generatingPlans ? text("generatingPlans") : text("generatePlans")}</span></button><button id="plan-generate-without-tours" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-200/30 bg-white/5 px-4 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10 ${state.generatingPlans ? "opacity-60" : ""}" ${state.generatingPlans ? "disabled" : ""}><i class="fa-solid fa-forward"></i><span>${text("continueWithoutTours")}</span></button></div></div>${state.loadingTours ? `<div class="flex min-h-[16rem] items-center justify-center border border-slate-200/20 bg-white/5 px-6 py-10 text-center text-slate-100"><div><i class="fa-solid fa-map-location-dot animate-pulse text-3xl"></i><p class="mt-4 text-base">${text("loadingTours")}</p></div></div>` : ""}${!state.loadingTours && !state.draft.tour_results.length ? `<div class="border border-slate-200/20 bg-white/5 px-6 py-10 text-center text-slate-100"><p>${state.draft.tour_empty_state ? escapeHtml(state.draft.tour_fallback?.summary || text("noTours")) : text("noTours")}</p></div>` : ""}${!state.loadingTours && state.draft.tour_results.length ? `<div class="grid gap-4 xl:grid-cols-2">${state.draft.tour_results.map(renderTourCard).join("")}</div>` : ""}</div>`;
    document.getElementById("plan-back-hotels")?.addEventListener("click", () => { state.step = "hotels"; render(); });
    document.getElementById("plan-generate-from-tours")?.addEventListener("click", generatePlanOptions);
    document.getElementById("plan-generate-without-tours")?.addEventListener("click", () => {
      state.draft.selected_tour_ids = [];
      saveDraft();
      generatePlanOptions();
    });
    modalBody.querySelectorAll("[data-plan-toggle-tour]").forEach((button) => {
      button.addEventListener("click", () => {
        const id = button.dataset.planToggleTour;
        const next = new Set(state.draft.selected_tour_ids);
        if (next.has(id)) next.delete(id); else next.add(id);
        state.draft.selected_tour_ids = Array.from(next);
        saveDraft();
        render();
      });
    });
  }

  function renderPlanOption(option) {
    const confirming = state.confirmingPlanId === option.plan_id;
    return `<article class="border border-slate-200/20 bg-white/5 p-5 text-slate-100"><div class="flex flex-col gap-4 border-b border-slate-200/10 pb-5 lg:flex-row lg:items-start lg:justify-between"><div><h3 class="font-display text-3xl text-slate-100">${escapeHtml(option.title || "Plan")}</h3><p class="mt-3 text-sm leading-6 text-slate-200">${escapeHtml(option.gemini_recommendation || option.summary || "")}</p></div><div class="min-w-[12rem] border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("estimatedTotal")}</p><p class="mt-2 text-base font-semibold text-slate-100">${escapeHtml(option.estimated_total || "-")} ${escapeHtml(option.currency || "TRY")}</p></div></div><div class="mt-5 space-y-4">${(option.days || []).map((day) => `<section class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">Day ${escapeHtml(day.day)}</p><div class="mt-4 space-y-3">${(day.timeline || []).map((item) => `<div class="grid gap-2 border border-slate-200/5 bg-white/[0.02] p-3 md:grid-cols-[5rem_minmax(0,1fr)] md:items-start"><span class="text-sm font-semibold text-lagoon-300">${escapeHtml(item.time)}</span><div><p class="text-sm font-semibold text-slate-100">${escapeHtml(item.title)}</p><p class="mt-1 text-sm text-slate-200">${escapeHtml(item.notes || "")}</p></div></div>`).join("")}</div></section>`).join("")}</div><button type="button" data-plan-confirm="${escapeHtml(option.plan_id)}" class="mt-6 inline-flex items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-5 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200 ${confirming ? "opacity-60" : ""}" ${confirming ? "disabled" : ""}><i class="fa-solid fa-check"></i><span>${confirming ? text("loadingPlan") : text("confirmPlan")}</span></button></article>`;
  }

  function renderPlansStep() {
    modalBody.innerHTML = `<div class="space-y-6"><div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_18rem]"><div class="border border-slate-200/20 bg-white/5 p-5 text-slate-100"><p class="text-xs uppercase tracking-[0.18em] text-slate-200">${text("selectedDestination")}</p><h3 class="mt-2 font-display text-3xl text-slate-100">${escapeHtml(state.draft.city)}</h3><p class="mt-2 text-sm text-slate-200">${escapeHtml(state.draft.selected_hotel_name)}</p><p class="mt-4 text-sm text-slate-200">${text("selectedTours")}: ${escapeHtml(state.draft.selected_tour_ids.length)}</p></div><button id="plan-back-tours" type="button" class="inline-flex h-fit items-center justify-center gap-2 border border-slate-200/30 px-4 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10"><i class="fa-solid fa-arrow-left"></i><span>${text("back")}</span></button></div>${state.draft.plan_options.length ? `<div class="grid gap-6 xl:grid-cols-2">${state.draft.plan_options.map(renderPlanOption).join("")}</div>` : `<div class="border border-slate-200/20 bg-white/5 px-6 py-10 text-center text-slate-100"><p>${text("noActivePlan")}</p></div>`}</div>`;
    document.getElementById("plan-back-tours")?.addEventListener("click", () => { state.step = "tours"; render(); });
    modalBody.querySelectorAll("[data-plan-confirm]").forEach((button) => {
      button.addEventListener("click", () => confirmPlan(button.dataset.planConfirm));
    });
  }

  function selectedPlan() {
    return state.draft.plan_options.find((item) => item.plan_id === state.draft.confirmed_plan_id) || state.draft.plan_options[0] || null;
  }

  function renderCompleteStep() {
    const option = selectedPlan();
    modalBody.innerHTML = `<div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]"><div class="space-y-5 border border-slate-200/20 bg-white/5 p-6 text-slate-100"><div><p class="text-sm uppercase tracking-[0.18em] text-slate-200">${text("selectedDestination")}</p><h3 class="mt-2 font-display text-3xl text-slate-100">${escapeHtml(state.draft.city)}</h3><p class="mt-3 text-sm text-slate-200">${escapeHtml(state.draft.selected_hotel_name)}</p></div><div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><div class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("startDate")}</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(state.draft.start_date)}</p></div><div class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("endDate")}</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(state.draft.end_date)}</p></div><div class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">${text("selectedTours")}</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(state.draft.selected_tour_ids.length)}</p></div><div class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">Plan ID</p><p class="mt-2 text-sm font-semibold text-slate-100">${escapeHtml(state.draft.confirmed_plan_id)}</p></div></div>${option ? `<div class="border border-slate-200/10 p-4"><p class="text-xs uppercase tracking-[0.16em] text-slate-300">Option</p><p class="mt-2 text-base font-semibold text-slate-100">${escapeHtml(option.title || "Plan")}</p><p class="mt-2 text-sm text-slate-200">${escapeHtml(option.gemini_recommendation || option.summary || "")}</p></div>` : ""}</div><div class="space-y-3"><a href="/hesabim/" class="inline-flex w-full items-center justify-center gap-2 border border-slate-100 bg-slate-100 px-5 py-3 text-sm font-semibold text-teal-700 transition hover:bg-slate-200">${text("goToAccount")}</a><button id="plan-create-another" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-200/30 bg-white/5 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10">${text("createAnotherPlan")}</button><button id="plan-complete-close" type="button" class="inline-flex w-full items-center justify-center gap-2 border border-slate-200/30 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:bg-white/10">${text("close")}</button></div></div>`;
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
    if (state.step === "hotels") return renderHotelsStep();
    if (state.step === "tours") return renderToursStep();
    if (state.step === "plans") return renderPlansStep();
    if (state.step === "complete") return renderCompleteStep();
    return renderDetailsStep();
  }

  async function prepareStep() {
    await ensureActivitiesLoaded();
    if (state.step === "hotels") await loadHotels();
    if (state.step === "tours") await loadTours();
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
    if (localStorage.getItem(RESUME_KEY) === "1" && hasMeaningfulDraft()) {
      localStorage.removeItem(RESUME_KEY);
      setFeedback(text("draftRestored"), "success");
      await openModal();
    }
  });
})();
