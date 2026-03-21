import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useLocale } from "../contexts/LocaleContext";
import { API } from "../services/apijs";
import "../styles/class-calendar.css";

const DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

/* ── Demo data: generated for a date range ─────────────────────── */
const DEMO_CLASSES = [
  { name: "Yoga Flow", instructor: "María López", duration: 60, capacity: 20 },
  { name: "HIIT Cardio", instructor: "Carlos Ruiz", duration: 45, capacity: 15 },
  { name: "Spinning", instructor: "Ana Torres", duration: 50, capacity: 25 },
  { name: "Pilates", instructor: "Sofía Herrera", duration: 55, capacity: 18 },
  { name: "CrossFit", instructor: "Diego Morales", duration: 60, capacity: 12 },
  { name: "Boxing", instructor: "Andrés Silva", duration: 45, capacity: 16 },
  { name: "Zumba", instructor: "Valentina Díaz", duration: 50, capacity: 30 },
  { name: "Stretching", instructor: "María López", duration: 30, capacity: 20 },
];
// Weekly pattern: [dayOfWeek 0=Mon, hour, classIndex]
const WEEKLY_SCHEDULE = [
  [0, 7, 0], [0, 9, 1], [0, 17, 2], [0, 19, 4],
  [1, 8, 3], [1, 10, 6], [1, 18, 1], [1, 20, 5],
  [2, 7, 0], [2, 9, 4], [2, 17, 2], [2, 19, 3],
  [3, 8, 6], [3, 10, 1], [3, 18, 5], [3, 20, 0],
  [4, 7, 4], [4, 9, 3], [4, 17, 1], [4, 19, 2],
  [5, 9, 6], [5, 11, 0], [5, 16, 7],
  [6, 10, 3], [6, 12, 7],
];

function generateDemoSessions(rangeStart, weeks = 1) {
  const results = [];
  let id = 1;
  for (let w = 0; w < weeks; w++) {
    for (const [dayOff, hour, ci] of WEEKLY_SCHEDULE) {
      const d = new Date(rangeStart);
      d.setDate(d.getDate() + w * 7 + dayOff);
      d.setHours(hour, 0, 0, 0);
      const c = DEMO_CLASSES[ci];
      results.push({
        id: id++,
        class_name: c.name,
        instructor: c.instructor,
        start_time: d.toISOString(),
        effective_duration: c.duration,
        effective_capacity: c.capacity,
        enrolled_count: Math.floor(Math.random() * c.capacity * 0.8),
      });
    }
  }
  return results;
}

function getWeekStart(date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function getMonthStart(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function getMonthEnd(date) {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0);
}

function formatTime(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function isSameDay(a, b) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

export default function ClassCalendarPage() {
  const { t } = useLocale();
  const { isAuthenticated } = useAuth();

  const [view, setView] = useState("week");
  const [currentDate, setCurrentDate] = useState(() => new Date());
  const [sessions, setSessions] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [selectedSession, setSelectedSession] = useState(null);
  const [actionStatus, setActionStatus] = useState("");

  const bookedSessionIds = useMemo(
    () => new Set(bookings.map((b) => b.session?.id ?? b.session_id)),
    [bookings],
  );

  const bookingBySession = useMemo(() => {
    const map = {};
    bookings.forEach((b) => {
      const sid = b.session?.id ?? b.session_id;
      if (sid != null) map[sid] = b;
    });
    return map;
  }, [bookings]);

  const weekStart = useMemo(() => getWeekStart(currentDate), [currentDate]);

  const calendarDays = useMemo(() => {
    if (view === "week") {
      return Array.from({ length: 7 }, (_, i) => {
        const d = new Date(weekStart);
        d.setDate(d.getDate() + i);
        return d;
      });
    }
    const mStart = getMonthStart(currentDate);
    const mEnd = getMonthEnd(currentDate);
    const startDay = mStart.getDay() === 0 ? 6 : mStart.getDay() - 1;
    const days = [];
    const first = new Date(mStart);
    first.setDate(first.getDate() - startDay);
    const totalCells = Math.ceil((startDay + mEnd.getDate()) / 7) * 7;
    for (let i = 0; i < totalCells; i++) {
      const d = new Date(first);
      d.setDate(d.getDate() + i);
      days.push(d);
    }
    return days;
  }, [view, currentDate, weekStart]);

  const sessionsByDay = useMemo(() => {
    const map = {};
    calendarDays.forEach((day) => {
      const key = day.toISOString().slice(0, 10);
      map[key] = [];
    });
    sessions.forEach((s) => {
      const d = new Date(s.start_time);
      const key = d.toISOString().slice(0, 10);
      if (map[key]) {
        map[key].push(s);
      }
    });
    return map;
  }, [sessions, calendarDays]);

  const loadData = useCallback(() => {
    setStatus("loading");
    setError("");
    const params = {};
    if (view === "week") {
      params.start = weekStart.toISOString().slice(0, 10);
      const end = new Date(weekStart);
      end.setDate(end.getDate() + 6);
      params.end = end.toISOString().slice(0, 10);
    } else {
      const mStart = getMonthStart(currentDate);
      const mEnd = getMonthEnd(currentDate);
      params.start = mStart.toISOString().slice(0, 10);
      params.end = mEnd.toISOString().slice(0, 10);
    }

    const qs = new URLSearchParams(params).toString();
    const sessionsPromise = API.classes.sessions(qs);
    const bookingsPromise = isAuthenticated
      ? API.classes.myBookings()
      : Promise.resolve([]);

    const demoStart = view === "week" ? weekStart : getWeekStart(getMonthStart(currentDate));
    const demoWeeks = view === "week" ? 1 : 6;

    Promise.all([sessionsPromise, bookingsPromise])
      .then(([sessData, bookData]) => {
        const list = Array.isArray(sessData) ? sessData : [];
        setSessions(list.length ? list : generateDemoSessions(demoStart, demoWeeks));
        setBookings(Array.isArray(bookData) ? bookData : []);
        setStatus("ready");
      })
      .catch(() => {
        setSessions(generateDemoSessions(demoStart, demoWeeks));
        setBookings([]);
        setStatus("ready");
      });
  }, [view, currentDate, weekStart, isAuthenticated, t]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const navigatePrev = useCallback(() => {
    setCurrentDate((prev) => {
      const d = new Date(prev);
      if (view === "week") {
        d.setDate(d.getDate() - 7);
      } else {
        d.setMonth(d.getMonth() - 1);
      }
      return d;
    });
  }, [view]);

  const navigateNext = useCallback(() => {
    setCurrentDate((prev) => {
      const d = new Date(prev);
      if (view === "week") {
        d.setDate(d.getDate() + 7);
      } else {
        d.setMonth(d.getMonth() + 1);
      }
      return d;
    });
  }, [view]);

  const navigateToday = useCallback(() => {
    setCurrentDate(new Date());
  }, []);

  const handleBook = useCallback(
    async (sessionId) => {
      if (!isAuthenticated) return;
      setActionStatus("");
      try {
        await API.classes.book(sessionId);
        setActionStatus(t("calendar.bookingSuccess"));
        loadData();
      } catch (err) {
        setActionStatus(err?.message || t("calendar.error"));
      }
    },
    [isAuthenticated, loadData, t],
  );

  const handleCancel = useCallback(
    async (sessionId) => {
      if (!isAuthenticated) return;
      setActionStatus("");
      const booking = bookingBySession[sessionId];
      if (!booking) return;
      try {
        await API.classes.cancelBooking(booking.id);
        setActionStatus(t("calendar.cancelSuccess"));
        loadData();
      } catch (err) {
        setActionStatus(err?.message || t("calendar.error"));
      }
    },
    [isAuthenticated, bookingBySession, loadData, t],
  );

  const closeModal = useCallback(() => {
    setSelectedSession(null);
    setActionStatus("");
  }, []);

  const today = useMemo(() => new Date(), []);

  return (
    <div className="class-calendar container py-4">
      <h1 className="mb-1">{t("calendar.title")}</h1>
      <p className="text-muted mb-4">{t("calendar.subtitle")}</p>

      {!isAuthenticated && (
        <div className="alert alert-warning mb-3">
          {t("calendar.loginRequired")}
        </div>
      )}

      <div className="class-calendar-controls mb-3">
        <div className="d-flex gap-2 align-items-center">
          <button
            className={`btn btn-sm ${view === "week" ? "btn-primary" : "btn-outline-primary"}`}
            onClick={() => setView("week")}
          >
            {t("calendar.weekView")}
          </button>
          <button
            className={`btn btn-sm ${view === "month" ? "btn-primary" : "btn-outline-primary"}`}
            onClick={() => setView("month")}
          >
            {t("calendar.monthView")}
          </button>
        </div>
        <div className="d-flex gap-2 align-items-center">
          <button className="btn btn-sm btn-outline-secondary" onClick={navigatePrev}>
            &laquo;
          </button>
          <button className="btn btn-sm btn-outline-secondary" onClick={navigateToday}>
            {t("calendar.today")}
          </button>
          <button className="btn btn-sm btn-outline-secondary" onClick={navigateNext}>
            &raquo;
          </button>
        </div>
      </div>

      {status === "loading" && (
        <div className="text-center py-5">
          <div className="spinner-border" role="status" />
          <p className="mt-2">{t("calendar.loading")}</p>
        </div>
      )}

      {status === "error" && (
        <div className="alert alert-danger">{error}</div>
      )}

      {status === "ready" && (
        <>
          <div className="class-calendar-grid">
            {DAY_KEYS.map((key) => (
              <div key={key} className="class-calendar-header">
                {t(`calendar.day.${key}`)}
              </div>
            ))}
            {calendarDays.map((day) => {
              const dateKey = day.toISOString().slice(0, 10);
              const daySessions = sessionsByDay[dateKey] || [];
              const isToday = isSameDay(day, today);
              const isCurrentMonth = day.getMonth() === currentDate.getMonth();
              return (
                <div
                  key={dateKey}
                  className={
                    "class-calendar-cell" +
                    (isToday ? " class-calendar-cell--today" : "") +
                    (!isCurrentMonth && view === "month"
                      ? " class-calendar-cell--outside"
                      : "")
                  }
                >
                  <span className="class-calendar-cell-date">{day.getDate()}</span>
                  {daySessions.length === 0 && (
                    <span className="class-calendar-cell-empty">
                      {t("calendar.noSessions")}
                    </span>
                  )}
                  {daySessions.map((session) => {
                    const isBooked = bookedSessionIds.has(session.id);
                    const isFull = session.enrolled_count >= session.capacity;
                    return (
                      <button
                        key={session.id}
                        type="button"
                        className={
                          "class-calendar-session" +
                          (isBooked ? " class-calendar-session--booked" : "") +
                          (isFull && !isBooked
                            ? " class-calendar-session--full"
                            : "")
                        }
                        onClick={() => setSelectedSession(session)}
                      >
                        <span className="class-calendar-session-name">
                          {session.class_name}
                        </span>
                        <span className="class-calendar-session-time">
                          {formatTime(session.start_time)}
                        </span>
                      </button>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </>
      )}

      {selectedSession && (
        <div className="class-calendar-modal" onClick={closeModal}>
          <div
            className="class-calendar-modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="class-calendar-modal-close"
              onClick={closeModal}
              aria-label="Close"
            >
              &times;
            </button>
            <h3>{selectedSession.class_name}</h3>
            <p>
              <strong>{t("calendar.instructor")}:</strong>{" "}
              {selectedSession.instructor}
            </p>
            <p>
              <strong>{t("calendar.time")}:</strong>{" "}
              {formatTime(selectedSession.start_time)} &ndash;{" "}
              {formatTime(selectedSession.end_time)}
            </p>
            <p>
              <strong>{t("calendar.capacity")}:</strong>{" "}
              {selectedSession.enrolled_count} / {selectedSession.capacity}
              {selectedSession.enrolled_count >= selectedSession.capacity && (
                <span className="badge bg-danger ms-2">{t("calendar.full")}</span>
              )}
            </p>

            {bookedSessionIds.has(selectedSession.id) && (
              <span className="badge bg-success mb-3 d-inline-block">
                {t("calendar.booked")}
              </span>
            )}

            {actionStatus && (
              <div className="alert alert-info mt-2 mb-2 py-2">{actionStatus}</div>
            )}

            {isAuthenticated ? (
              <div className="d-flex gap-2 mt-3">
                {bookedSessionIds.has(selectedSession.id) ? (
                  <button
                    className="btn btn-outline-danger"
                    onClick={() => handleCancel(selectedSession.id)}
                  >
                    {t("calendar.cancelBooking")}
                  </button>
                ) : (
                  <button
                    className="btn btn-primary"
                    disabled={
                      selectedSession.enrolled_count >= selectedSession.capacity
                    }
                    onClick={() => handleBook(selectedSession.id)}
                  >
                    {t("calendar.book")}
                  </button>
                )}
              </div>
            ) : (
              <div className="alert alert-warning mt-3 mb-0">
                {t("calendar.loginRequired")}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
