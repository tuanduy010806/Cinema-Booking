const API = "/api/v1";
const TOKEN_KEY = "cinema_booking_access_token";

const state = {
  token: localStorage.getItem(TOKEN_KEY),
  user: null,
  movies: [],
  selectedMovie: null,
  selectedShowtime: null,
  selectedSeat: null,
  authMode: "login",
  toastTimer: null,
};

const elements = {
  authStatus: document.querySelector("#auth-status"),
  authOpen: document.querySelector("#auth-open"),
  logout: document.querySelector("#logout-button"),
  authDialog: document.querySelector("#auth-dialog"),
  authForm: document.querySelector("#auth-form"),
  authTitle: document.querySelector("#auth-title"),
  authEmail: document.querySelector("#auth-email"),
  authPassword: document.querySelector("#auth-password"),
  repassword: document.querySelector("#auth-repassword"),
  repasswordField: document.querySelector("#repassword-field"),
  authSubmit: document.querySelector("#auth-submit"),
  authMessage: document.querySelector("#auth-message"),
  movieList: document.querySelector("#movie-list"),
  showtimesSection: document.querySelector("#showtimes-section"),
  showtimeList: document.querySelector("#showtime-list"),
  selectedMovieTitle: document.querySelector("#selected-movie-title"),
  selectedMovieMeta: document.querySelector("#selected-movie-meta"),
  seatsSection: document.querySelector("#seats-section"),
  selectedShowtimeLabel: document.querySelector("#selected-showtime-label"),
  seatGrid: document.querySelector("#seat-grid"),
  chosenSeatLabel: document.querySelector("#chosen-seat-label"),
  bookButton: document.querySelector("#book-button"),
  bookingList: document.querySelector("#booking-list"),
  toast: document.querySelector("#toast"),
  adminNav: document.querySelector("#admin-nav"),
  adminPanel: document.querySelector("#admin-panel"),
  movieCreateForm: document.querySelector("#movie-create-form"),
  movieEditForm: document.querySelector("#movie-edit-form"),
  showtimeCreateForm: document.querySelector("#showtime-create-form"),
  showtimeMovieId: document.querySelector("#showtime-movie-id"),
  adminMovieList: document.querySelector("#admin-movie-list"),
  adminMessage: document.querySelector("#admin-message"),
};

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body) headers.set("Content-Type", "application/json");
  if (state.token) headers.set("Authorization", `Bearer ${state.token}`);

  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (state.token && response.status === 401 && !["/auth/login", "/auth/register"].includes(path)) {
    clearSession();
  }

  if (!response.ok) {
    let message = `Yêu cầu thất bại (${response.status})`;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch { /* Response body may be empty. */ }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

function setSession(token) {
  state.token = token;
  localStorage.setItem(TOKEN_KEY, token);
}

function clearSession() {
  state.token = null;
  state.user = null;
  localStorage.removeItem(TOKEN_KEY);
  updateAccountUI();
  renderBookings([]);
}

function updateAccountUI() {
  const signedIn = Boolean(state.token);
  elements.authStatus.textContent = signedIn
    ? (state.user?.role === "ADMIN" ? "Quản trị viên" : "Đã đăng nhập")
    : "Chưa đăng nhập";
  elements.authOpen.classList.toggle("hidden", signedIn);
  elements.logout.classList.toggle("hidden", !signedIn);
  const isAdmin = signedIn && state.user?.role === "ADMIN";
  elements.adminNav.classList.toggle("hidden", !isAdmin);
  elements.adminPanel.classList.toggle("hidden", !isAdmin);
  elements.bookButton.disabled = !state.selectedSeat;
}

async function loadCurrentUser() {
  if (!state.token) {
    state.user = null;
    updateAccountUI();
    return null;
  }
  state.user = await api("/auth/me");
  updateAccountUI();
  return state.user;
}

function showToast(message, isError = false) {
  elements.toast.textContent = message;
  elements.toast.style.borderColor = isError ? "#704242" : "#565860";
  elements.toast.classList.add("visible");
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => elements.toast.classList.remove("visible"), 3200);
}

function showError(container, message) {
  container.innerHTML = "";
  const note = document.createElement("div");
  note.className = "empty-state";
  note.textContent = message;
  container.append(note);
}

function formatDate(value, options = {}) {
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
    ...options,
  }).format(new Date(value));
}

async function loadMovies() {
  elements.movieList.innerHTML = '<div class="empty-state">Đang tải danh sách phim…</div>';
  try {
    state.movies = await api("/movies");
    renderMovies();
    renderAdminMovies();
  } catch (error) {
    showError(elements.movieList, `${error.message}. Hãy kiểm tra API và database.`);
  }
}

function renderMovies() {
  if (!state.movies.length) {
    showError(elements.movieList, "Chưa có phim nào trong hệ thống.");
    return;
  }
  elements.movieList.innerHTML = "";
  state.movies.forEach((movie, index) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = `movie-card${state.selectedMovie?.id === movie.id ? " selected" : ""}`;
    card.setAttribute("aria-pressed", state.selectedMovie?.id === movie.id);

    const number = document.createElement("span");
    number.className = "movie-index";
    number.textContent = `PHIM ${String(index + 1).padStart(2, "0")}`;
    const title = document.createElement("h3");
    title.textContent = movie.title;
    const description = document.createElement("p");
    description.textContent = movie.description || "Thông tin phim chưa được cập nhật.";
    const duration = document.createElement("span");
    duration.className = "movie-duration";
    duration.textContent = `${movie.duration_minutes} phút`;
    card.append(number, title, description, duration);
    card.addEventListener("click", () => selectMovie(movie));
    elements.movieList.append(card);
  });
}

async function selectMovie(movie) {
  state.selectedMovie = movie;
  state.selectedShowtime = null;
  state.selectedSeat = null;
  renderMovies();
  elements.showtimesSection.classList.remove("hidden");
  elements.seatsSection.classList.add("hidden");
  elements.selectedMovieTitle.textContent = movie.title;
  elements.selectedMovieMeta.textContent = `${movie.duration_minutes} phút`;
  elements.showtimeList.innerHTML = '<div class="empty-state">Đang tải suất chiếu…</div>';
  elements.showtimesSection.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const showtimes = await api(`/showtimes?movie_id=${encodeURIComponent(movie.id)}`);
    renderShowtimes(showtimes);
  } catch (error) {
    showError(elements.showtimeList, error.message);
  }
}

function renderShowtimes(showtimes) {
  if (!showtimes.length) {
    showError(elements.showtimeList, "Phim này chưa có suất chiếu.");
    return;
  }
  elements.showtimeList.innerHTML = "";
  showtimes.forEach((showtime) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "showtime-card";
    const date = document.createElement("strong");
    date.textContent = formatDate(showtime.start_time);
    const capacity = document.createElement("span");
    capacity.textContent = `${showtime.total_seats} ghế`;
    button.append(date, capacity);
    button.addEventListener("click", () => selectShowtime(showtime, button));
    elements.showtimeList.append(button);
  });
}

async function selectShowtime(showtime, button) {
  state.selectedShowtime = showtime;
  state.selectedSeat = null;
  elements.showtimeList.querySelectorAll(".showtime-card").forEach((item) => item.classList.remove("selected"));
  button.classList.add("selected");
  elements.seatsSection.classList.remove("hidden");
  elements.selectedShowtimeLabel.textContent = formatDate(showtime.start_time);
  elements.seatGrid.innerHTML = '<div class="empty-state">Đang tải sơ đồ ghế…</div>';
  updateSeatSelection();
  elements.seatsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const seats = await api(`/showtimes/${showtime.id}/seats`);
    renderSeats(seats);
  } catch (error) {
    showError(elements.seatGrid, error.message);
  }
}

function renderSeats(seats) {
  elements.seatGrid.innerHTML = "";
  seats.forEach((seat) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "seat";
    button.textContent = seat.seat_number;
    button.setAttribute("aria-label", `Ghế ${seat.seat_number}${seat.is_available ? ", còn trống" : ", đã đặt"}`);
    button.disabled = !seat.is_available;
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
      state.selectedSeat = state.selectedSeat === seat.seat_number ? null : seat.seat_number;
      renderSeats(seats);
      updateSeatSelection();
    });
    if (state.selectedSeat === seat.seat_number) {
      button.classList.add("selected");
      button.setAttribute("aria-pressed", "true");
    }
    elements.seatGrid.append(button);
  });
}

function updateSeatSelection() {
  elements.chosenSeatLabel.textContent = state.selectedSeat ? `Ghế ${state.selectedSeat}` : "Chưa chọn";
  elements.bookButton.disabled = !state.selectedSeat;
}

async function bookSelectedSeat() {
  if (!state.selectedShowtime || !state.selectedSeat) return;
  if (!state.token) {
    openAuthDialog("login");
    return;
  }
  elements.bookButton.disabled = true;
  try {
    await api("/bookings/", {
      method: "POST",
      body: JSON.stringify({
        showtime_id: state.selectedShowtime.id,
        seat_number: state.selectedSeat,
      }),
    });
    showToast(`Đã đặt ghế ${state.selectedSeat}.`);
    state.selectedSeat = null;
    await Promise.all([loadBookings(), selectShowtime(state.selectedShowtime, elements.showtimeList.querySelector(".selected"))]);
  } catch (error) {
    showToast(error.message, true);
    elements.bookButton.disabled = false;
  }
}

async function loadBookings() {
  if (!state.token) {
    renderBookings([]);
    return;
  }
  elements.bookingList.innerHTML = '<div class="empty-state">Đang tải vé…</div>';
  try {
    const bookings = await api("/bookings/me");
    renderBookings(bookings);
  } catch (error) {
    if (state.token) showError(elements.bookingList, error.message);
  }
}

function renderBookings(bookings) {
  if (!state.token) {
    showError(elements.bookingList, "Đăng nhập để xem các vé đã đặt.");
    return;
  }
  if (!bookings.length) {
    showError(elements.bookingList, "Bạn chưa có vé nào. Chọn một suất chiếu để đặt vé.");
    return;
  }
  elements.bookingList.innerHTML = "";
  bookings.forEach((booking) => {
    const card = document.createElement("article");
    card.className = "booking-card";
    const info = document.createElement("div");
    const title = document.createElement("strong");
    const movie = state.movies.find((item) => item.id === booking.movie_id);
    title.textContent = movie ? movie.title : `Suất chiếu #${booking.showtime_id}`;
    const detail = document.createElement("small");
    detail.textContent = `Vé #${booking.id} · Ghế ${booking.seat_number} · Suất chiếu #${booking.showtime_id}`;
    const status = document.createElement("span");
    status.className = `booking-status${booking.status === "cancelled" ? " cancelled" : ""}`;
    status.textContent = booking.status === "active" ? "Đang hiệu lực" : "Đã hủy";
    info.append(title, detail, status);
    card.append(info);

    if (booking.status === "active") {
      const cancel = document.createElement("button");
      cancel.type = "button";
      cancel.className = "cancel-button";
      cancel.textContent = "Hủy vé";
      cancel.addEventListener("click", () => cancelBooking(booking.id));
      card.append(cancel);
    }
    elements.bookingList.append(card);
  });
}

async function cancelBooking(bookingId) {
  if (!window.confirm(`Bạn muốn hủy vé #${bookingId}?`)) return;
  try {
    await api(`/bookings/${bookingId}`, { method: "DELETE" });
    showToast(`Đã hủy vé #${bookingId}.`);
    await Promise.all([loadBookings(), state.selectedShowtime ? refreshSelectedSeats() : Promise.resolve()]);
  } catch (error) {
    showToast(error.message, true);
  }
}

async function refreshSelectedSeats() {
  try {
    const seats = await api(`/showtimes/${state.selectedShowtime.id}/seats`);
    state.selectedSeat = null;
    renderSeats(seats);
    updateSeatSelection();
  } catch (error) {
    showToast(error.message, true);
  }
}

function openAuthDialog(mode = "login") {
  setAuthMode(mode);
  elements.authMessage.textContent = "";
  elements.authMessage.className = "form-message";
  elements.authDialog.showModal();
}

function setAuthMode(mode) {
  state.authMode = mode;
  const registering = mode === "register";
  elements.authTitle.textContent = registering ? "Tạo tài khoản mới" : "Chào mừng trở lại";
  elements.authSubmit.textContent = registering ? "Đăng ký" : "Đăng nhập";
  elements.repasswordField.classList.toggle("hidden", !registering);
  elements.repassword.required = registering;
  elements.authPassword.autocomplete = registering ? "new-password" : "current-password";
  document.querySelectorAll(".auth-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.mode === mode));
}

async function submitAuth(event) {
  event.preventDefault();
  const registering = state.authMode === "register";
  const payload = {
    email: elements.authEmail.value.trim(),
    password: elements.authPassword.value,
  };
  if (registering) payload.repassword = elements.repassword.value;

  elements.authSubmit.disabled = true;
  elements.authMessage.textContent = "Đang xử lý…";
  elements.authMessage.className = "form-message";
  try {
    const result = await api(`/auth/${registering ? "register" : "login"}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setSession(result.access_token);
    await loadCurrentUser();
    elements.authDialog.close();
    elements.authForm.reset();
    showToast(registering ? "Tạo tài khoản thành công." : "Đăng nhập thành công.");
    await Promise.all([loadBookings(), state.user?.role === "ADMIN" ? loadMovies() : Promise.resolve()]);
    updateSeatSelection();
  } catch (error) {
    elements.authMessage.textContent = error.message;
    elements.authMessage.className = "form-message error";
  } finally {
    elements.authSubmit.disabled = false;
  }
}

function setAdminMessage(message, isError = false) {
  elements.adminMessage.textContent = message;
  elements.adminMessage.className = `form-message${isError ? " error" : " success"}`;
}

function renderAdminMovies() {
  if (state.user?.role !== "ADMIN") return;
  elements.adminMovieList.replaceChildren();
  elements.showtimeMovieId.replaceChildren();

  if (!state.movies.length) {
    showError(elements.adminMovieList, "Chưa có phim để quản lý hoặc tạo suất chiếu.");
    return;
  }

  for (const movie of state.movies) {
    const option = document.createElement("option");
    option.value = movie.id;
    option.textContent = movie.title;
    elements.showtimeMovieId.append(option);

    const card = document.createElement("article");
    card.className = "admin-movie-card";
    const info = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = movie.title;
    const detail = document.createElement("small");
    detail.textContent = `${movie.duration_minutes} phút · ID ${movie.id}`;
    info.append(title, detail);

    const actions = document.createElement("div");
    actions.className = "admin-actions";
    const edit = document.createElement("button");
    edit.type = "button";
    edit.className = "button button-outline";
    edit.textContent = "Sửa";
    edit.addEventListener("click", () => openMovieEditor(movie));
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "cancel-button";
    remove.textContent = "Xóa";
    remove.addEventListener("click", () => deleteMovie(movie));
    actions.append(edit, remove);
    card.append(info, actions);
    elements.adminMovieList.append(card);
  }
}

function openMovieEditor(movie) {
  const form = elements.movieEditForm;
  form.elements.movie_id.value = movie.id;
  form.elements.title.value = movie.title;
  form.elements.description.value = movie.description || "";
  form.elements.duration_minutes.value = movie.duration_minutes;
  form.classList.remove("hidden");
  form.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function deleteMovie(movie) {
  if (!window.confirm(`Xóa phim “${movie.title}”?`)) return;
  try {
    await api(`/movies/${movie.id}`, { method: "DELETE" });
    setAdminMessage(`Đã xóa phim “${movie.title}”.`);
    await loadMovies();
  } catch (error) {
    setAdminMessage(error.message, true);
  }
}

elements.movieCreateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  try {
    const movie = await api("/movies", {
      method: "POST",
      body: JSON.stringify({
        title: data.get("title").trim(),
        description: data.get("description").trim() || null,
        duration_minutes: Number(data.get("duration_minutes")),
      }),
    });
    form.reset();
    setAdminMessage(`Đã thêm phim “${movie.title}”.`);
    await loadMovies();
  } catch (error) {
    setAdminMessage(error.message, true);
  }
});

elements.movieEditForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const movieId = data.get("movie_id");
  try {
    const movie = await api(`/movies/${movieId}`, {
      method: "PUT",
      body: JSON.stringify({
        title: data.get("title").trim(),
        description: data.get("description").trim() || null,
        duration_minutes: Number(data.get("duration_minutes")),
      }),
    });
    form.classList.add("hidden");
    setAdminMessage(`Đã cập nhật phim “${movie.title}”.`);
    await loadMovies();
  } catch (error) {
    setAdminMessage(error.message, true);
  }
});

elements.showtimeCreateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  try {
    const showtime = await api("/showtimes", {
      method: "POST",
      body: JSON.stringify({
        movie_id: Number(data.get("movie_id")),
        start_time: data.get("start_time"),
        total_seats: Number(data.get("total_seats")),
      }),
    });
    form.reset();
    setAdminMessage(`Đã tạo suất chiếu #${showtime.id}.`);
  } catch (error) {
    setAdminMessage(error.message, true);
  }
});

document.querySelector("#movie-edit-cancel").addEventListener("click", () => {
  elements.movieEditForm.classList.add("hidden");
});
document.querySelector("#admin-refresh-movies").addEventListener("click", loadMovies);

elements.authOpen.addEventListener("click", () => openAuthDialog("login"));
elements.logout.addEventListener("click", () => {
  clearSession();
  updateSeatSelection();
  showToast("Bạn đã đăng xuất.");
});
document.querySelector("#auth-close").addEventListener("click", () => elements.authDialog.close());
document.querySelectorAll(".auth-tab").forEach((tab) => tab.addEventListener("click", () => setAuthMode(tab.dataset.mode)));
elements.authForm.addEventListener("submit", submitAuth);
elements.bookButton.addEventListener("click", bookSelectedSeat);
document.querySelector("#refresh-movies").addEventListener("click", loadMovies);
document.querySelector("#refresh-bookings").addEventListener("click", loadBookings);

async function initializeApp() {
  if (state.token) {
    try {
      await loadCurrentUser();
    } catch {
      // api() clears an expired or invalid session.
    }
  } else {
    updateAccountUI();
  }
  await Promise.all([loadMovies(), loadBookings()]);
}

initializeApp();
