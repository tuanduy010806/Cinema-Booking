const API = "/api/v1";
const TOKEN_KEY = "cinema_booking_access_token";

const state = {
  token: localStorage.getItem(TOKEN_KEY),
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
};

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body) headers.set("Content-Type", "application/json");
  if (state.token) headers.set("Authorization", `Bearer ${state.token}`);

  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (state.token && response.status === 401 && !path.startsWith("/auth/")) {
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
  updateAccountUI();
}

function clearSession() {
  state.token = null;
  localStorage.removeItem(TOKEN_KEY);
  updateAccountUI();
  renderBookings([]);
}

function updateAccountUI() {
  const signedIn = Boolean(state.token);
  elements.authStatus.textContent = signedIn ? "Đã đăng nhập" : "Chưa đăng nhập";
  elements.authOpen.classList.toggle("hidden", signedIn);
  elements.logout.classList.toggle("hidden", !signedIn);
  elements.bookButton.disabled = !state.selectedSeat;
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
    elements.authDialog.close();
    elements.authForm.reset();
    showToast(registering ? "Tạo tài khoản thành công." : "Đăng nhập thành công.");
    await loadBookings();
    updateSeatSelection();
  } catch (error) {
    elements.authMessage.textContent = error.message;
    elements.authMessage.className = "form-message error";
  } finally {
    elements.authSubmit.disabled = false;
  }
}

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

updateAccountUI();
loadMovies();
loadBookings();
