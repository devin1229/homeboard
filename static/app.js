function updateDateAndTime() {
  const now = new Date();

  // -------------------------
  // Date formatting
  // -------------------------

  const dateOptions = {
    weekday: "long",
    month: "long",
    day: "numeric",
  };

  const normalDate = now.toLocaleDateString("en-US", dateOptions);

  const upperDate = normalDate.toUpperCase();

  // -------------------------
  // Main dashboard date
  // -------------------------

  const currentDate = document.getElementById("current-date");

  if (currentDate) {
    currentDate.textContent = upperDate;
  }

  // -------------------------
  // Greeting
  // -------------------------

  const hour = now.getHours();

  let greeting;

  if (hour < 12) {
    greeting = "Good morning.";
  } else if (hour < 17) {
    greeting = "Good afternoon.";
  } else {
    greeting = "Good evening.";
  }

  const greetingElement = document.getElementById("greeting");

  if (greetingElement) {
    greetingElement.textContent = greeting;
  }

  // -------------------------
  // Time formatting
  // -------------------------

  const timeOptions = {
    hour: "numeric",
    minute: "2-digit",
  };

  const currentTime = now.toLocaleTimeString("en-US", timeOptions);

  // -------------------------
  // Footer clock
  // -------------------------

  const liveClock = document.getElementById("live-clock");

  if (liveClock) {
    liveClock.textContent = currentTime;
  }

  // -------------------------
  // Ambient clock
  // -------------------------

  const ambientTime = document.getElementById("ambient-time");

  const ambientDate = document.getElementById("ambient-date");

  if (ambientTime) {
    ambientTime.textContent = currentTime;
  }

  if (ambientDate) {
    ambientDate.textContent = normalDate;
  }
}

// Run immediately

updateDateAndTime();

// Keep clocks current
setInterval(updateDateAndTime, 1000);

/* ------------------------------
   Ambient Mode Cycle
------------------------------ */

async function refreshAmbientData() {
  try {
    const response = await fetch("/api/ambient");

    if (!response.ok) {
      throw new Error("Ambient update failed");
    }

    const data = await response.json();

    // Update weather
    const weatherIcon = document.querySelector(".ambient-weather-icon");

    const weatherTemp = document.querySelector(".ambient-temperature");

    const weatherCondition = document.querySelector(".ambient-condition");

    if (data.weather && data.weather.available) {
      weatherIcon.textContent = getWeatherSymbol(data.weather.icon);

      weatherTemp.textContent = `${data.weather.temperature}°`;

      weatherCondition.textContent = data.weather.condition;
    }

    // Update next event
    const nextEvent = document.querySelector(".ambient-next-event");

    const nextLabel = document.querySelector(".ambient-next-label");

    if (data.current_event) {
      nextLabel.textContent = "NOW";

      let eventText = data.current_event.title;

      if (data.current_event.all_day) {
        eventText += " · All day";
      } else if (data.current_event.end_time) {
        eventText += ` · Until ${formatEventTime(data.current_event.end_time)}`;
      }

      nextEvent.textContent = eventText;
    } else if (data.next_event) {
      nextLabel.textContent = "UP NEXT";

      let eventText = data.next_event.title;

      if (data.next_event.all_day) {
        eventText += " · All day";
      } else if (data.next_event.start_time) {
        eventText += ` · ${formatEventTime(data.next_event.start_time)}`;
      }

      nextEvent.textContent = eventText;
    } else {
      nextLabel.textContent = "UP NEXT";
      nextEvent.textContent = "Nothing coming up";
    }
  } catch (error) {
    console.error("Could not refresh ambient data:", error);
  }
}

function getWeatherSymbol(icon) {
  const symbols = {
    clear: "☀︎",
    "partly-cloudy": "☀︎",
    cloudy: "☁︎",
    fog: "≋",
    drizzle: "☂︎",
    rain: "☂︎",
    snow: "❄︎",
    thunderstorm: "ϟ",
  };

  return symbols[icon] || "☁︎";
}

function formatEventTime(time) {
  const [hourString, minute] = time.split(":");

  let hour = parseInt(hourString, 10);

  const period = hour >= 12 ? "PM" : "AM";

  hour = hour % 12 || 12;

  return `${hour}:${minute} ${period}`;
}

const ambientMode = document.getElementById("ambient-mode");
const ambientContent = document.querySelector(".ambient-content");

const ambientPositions = [
  "position-center",
  "position-upper-left",
  "position-upper-right",
  "position-lower-left",
  "position-lower-right",
];

let lastPosition = -1;
let ambientTimer;
let ambientReturnTimer;

const AMBIENT_IDLE_DELAY = 2 * 60 * 1000;
const AMBIENT_DURATION = 60 * 1000;

function showAmbientMode() {
  refreshAmbientData();

  let newPosition;

  do {
    newPosition = Math.floor(Math.random() * ambientPositions.length);
  } while (newPosition === lastPosition && ambientPositions.length > 1);

  ambientPositions.forEach((position) => {
    ambientContent.classList.remove(position);
  });

  ambientContent.classList.add(ambientPositions[newPosition]);

  lastPosition = newPosition;

  ambientMode.classList.add("active");

  clearTimeout(ambientReturnTimer);

  ambientReturnTimer = setTimeout(() => {
    hideAmbientMode();
    resetAmbientTimer();
  }, AMBIENT_DURATION);
}

function hideAmbientMode() {
  clearTimeout(ambientReturnTimer);
  ambientMode.classList.remove("active");
}

function resetAmbientTimer() {
  clearTimeout(ambientTimer);

  if (ambientMode.classList.contains("active")) {
    hideAmbientMode();
  }

  ambientTimer = setTimeout(showAmbientMode, AMBIENT_IDLE_DELAY);
}

const activityEvents = ["click", "touchstart", "keydown"];

activityEvents.forEach((eventName) => {
  document.addEventListener(eventName, resetAmbientTimer);
});

resetAmbientTimer();

/* ------------------------------
   Day/Night Brightness Control
------------------------------ */

function updateBrightness() {
  const hour = new Date().getHours();

  document.body.classList.remove(
    "brightness-day",
    "brightness-evening",
    "brightness-night",
  );

  if (hour >= 9 && hour < 18) {
    document.body.classList.add("brightness-day");
  } else if ((hour >= 18 && hour < 22) || (hour >= 6 && hour < 9)) {
    document.body.classList.add("brightness-evening");
  } else {
    document.body.classList.add("brightness-night");
  }
}

updateBrightness();
setInterval(updateBrightness, 60000);

/* ------------------------------
   Live Shopping Updates + Pagination
------------------------------ */

let shoppingItems = [];
let shoppingPages = [];
let currentShoppingPage = 0;

const SHOPPING_PAGE_DURATION = 8000;
const SHOPPING_WIDTH_BUDGET = 760;

function estimateItemWidth(name) {
  const baseWidth = 38;
  const characterWidth = 8.5;
  return baseWidth + name.length * characterWidth;
}

function buildShoppingPages(items) {
  const pages = [];
  let currentPage = [];
  let currentWidth = 0;

  items.forEach((item) => {
    const itemWidth = estimateItemWidth(item.name);
    if (
      currentPage.length > 0 &&
      currentWidth + itemWidth > SHOPPING_WIDTH_BUDGET
    ) {
      pages.push(currentPage);
      currentPage = [];
      currentWidth = 0;
    }
    currentPage.push(item);
    currentWidth += itemWidth + 10;
  });
  if (currentPage.length > 0) {
    pages.push(currentPage);
  }
  return pages;
}

function renderShoppingPage() {
  const shoppingGrid = document.getElementById("shopping-grid");
  const pageIndicator = document.getElementById("shopping-page-indicator");

  if (!shoppingGrid || !pageIndicator) {
    return;
  }

  shoppingGrid.innerHTML = "";

  if (shoppingPages.length === 0) {
    pageIndicator.style.display = "none";
    return;
  }

  const page = shoppingPages[currentShoppingPage];

  page.forEach((item) => {
    const itemElement = document.createElement("div");
    itemElement.className = "shopping-item";
    itemElement.textContent = item.name;
    shoppingGrid.appendChild(itemElement);
  });

  if (shoppingPages.length > 1) {
    pageIndicator.style.display = "inline-block";
    pageIndicator.textContent = `${currentShoppingPage + 1} of ${shoppingPages.length}`;
  } else {
    pageIndicator.style.display = "none";
  }
}

function moveToNextShoppingPage() {
  if (shoppingPages.length <= 1) {
    return;
  }

  const shoppingGrid = document.getElementById("shopping-grid");

  shoppingGrid.classList.add("page-fade");

  setTimeout(() => {
    currentShoppingPage = (currentShoppingPage + 1) % shoppingPages.length;
    renderShoppingPage();
    shoppingGrid.classList.remove("page-fade");
  }, 350);
}

async function updateShoppingList() {
  try {
    const response = await fetch("/api/shopping");
    if (!response.ok) {
      throw new Error("Shopping update failed");
    }
    const items = await response.json();
    const shoppingCount = document.getElementById("shopping-count");
    shoppingItems = items;
    shoppingPages = buildShoppingPages(shoppingItems);

    if (currentShoppingPage >= shoppingPages.length) {
      currentShoppingPage = 0;
    }

    renderShoppingPage();

    if (shoppingCount) {
      shoppingCount.textContent = `${items.length} ${
        items.length === 1 ? "item" : "items"
      }`;
    }
  } catch (error) {
    console.error("Could not update shopping list:", error);
  }
}

// Load immediately
updateShoppingList();

// Check database every 10 seconds
setInterval(updateShoppingList, 10000);

// Rotate shopping pages every 8 seconds
setInterval(moveToNextShoppingPage, SHOPPING_PAGE_DURATION);

/* ------------------------------
   Live Task Updates
------------------------------ */

const MAX_DASHBOARD_TASKS = 4;

function getTaskAssigneeLabel(assignee) {
  if (assignee === "Devin") {
    return "D";
  }
  if (assignee === "Mom") {
    return "M";
  }
  if (assignee === "Garrett") {
    return "G";
  }
  return "⌂";
}

function formatTaskDueDate(dueDate) {
  if (!dueDate) {
    return "";
  }

  const date = new Date(`${dueDate}T00:00:00`);

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function renderDashboardTasks(tasks) {
  const taskList = document.getElementById("task-list");

  const taskCount = document.getElementById("task-count");

  if (!taskList || !taskCount) {
    return;
  }

  taskList.innerHTML = "";

  const visibleTasks = tasks.slice(0, MAX_DASHBOARD_TASKS);

  visibleTasks.forEach((task) => {
    const taskRow = document.createElement("div");

    taskRow.className = "task-item";

    const taskCircle = document.createElement("span");

    taskCircle.className = "task-circle";

    const taskName = document.createElement("span");

    taskName.className = "task-name";
    taskName.textContent = task.name;

    const taskMeta = document.createElement("span");

    taskMeta.className = "task-meta";

    const assignee = document.createElement("span");

    assignee.className = "task-assignee";
    assignee.textContent = getTaskAssigneeLabel(task.assignee);

    taskMeta.appendChild(assignee);

    if (task.due_date) {
      const dueDate = document.createElement("span");

      dueDate.className = "task-due";

      if (task.status === "overdue") {
        dueDate.classList.add("overdue");
        dueDate.textContent = "OVERDUE";
      } else if (task.status === "today") {
        dueDate.classList.add("today");
        dueDate.textContent = "TODAY";
      } else {
        dueDate.textContent = formatTaskDueDate(task.due_date);
      }

      taskMeta.appendChild(dueDate);
    }

    taskRow.appendChild(taskCircle);
    taskRow.appendChild(taskName);
    taskRow.appendChild(taskMeta);
    taskList.appendChild(taskRow);
  });

  if (tasks.length === 0) {
    const emptyMessage = document.createElement("div");

    emptyMessage.className = "task-empty";

    emptyMessage.textContent = "Nothing on the list.";

    taskList.appendChild(emptyMessage);

    taskCount.textContent = "0 remaining";

    return;
  }

  if (tasks.length > MAX_DASHBOARD_TASKS) {
    taskCount.textContent = `${MAX_DASHBOARD_TASKS} of ${tasks.length}`;
  } else {
    taskCount.textContent = `${tasks.length} remaining`;
  }
}

async function updateDashboardTasks() {
  try {
    const response = await fetch("api/tasks");

    if (!response.ok) {
      throw new Error("Task update failed");
    }

    const tasks = await response.json();

    renderDashboardTasks(tasks);
  } catch (error) {
    console.error("Could not update tasks:", error);
  }
}

/* ------------------------------
   Schedule Pagination
------------------------------ */

const SCHEDULE_ITEMS_PER_PAGE = 3;
const SCHEDULE_PAGE_DURATION = 8000;

let schedulePages = [];
let currentSchedulePage = 0;

function buildSchedulePages() {
  const scheduleList = document.getElementById("schedule-list");

  if (!scheduleList) {
    return;
  }

  const scheduleItems = Array.from(
    scheduleList.querySelectorAll(".schedule-item"),
  );

  schedulePages = [];

  for (let i = 0; i < scheduleItems.length; i += SCHEDULE_ITEMS_PER_PAGE) {
    schedulePages.push(scheduleItems.slice(i, i + SCHEDULE_ITEMS_PER_PAGE));
  }
}

function renderSchedulePage() {
  const scheduleList = document.getElementById("schedule-list");
  const pageIndicator = document.getElementById("schedule-page-indicator");

  if (!scheduleList || !pageIndicator) {
    return;
  }

  const allItems = scheduleList.querySelectorAll(".schedule-item");

  allItems.forEach((item) => {
    item.style.display = "none";
  });

  if (schedulePages.length === 0) {
    pageIndicator.style.display = "none";
    return;
  }

  schedulePages[currentSchedulePage].forEach((item) => {
    item.style.display = "";
  });

  if (schedulePages.length > 1) {
    pageIndicator.style.display = "inline-block";
    pageIndicator.textContent = `${currentSchedulePage + 1} of ${schedulePages.length}`;
  } else {
    pageIndicator.style.display = "none";
  }
}

function moveToNextSchedulePage() {
  if (schedulePages.length <= 1) {
    return;
  }

  const scheduleList = document.getElementById("schedule-list");

  if (!scheduleList) {
    return;
  }

  scheduleList.classList.add("page-fade");

  setTimeout(() => {
    currentSchedulePage = (currentSchedulePage + 1) % schedulePages.length;
    renderSchedulePage();
    scheduleList.classList.remove("page-fade");
  }, 350);
}

/* ------------------------------
   Live Calendar Updates
------------------------------ */

function renderTodayEvents(events) {
  const scheduleList = document.getElementById("schedule-list");

  if (!scheduleList) {
    return;
  }

  scheduleList.innerHTML = "";

  if (events.length === 0) {
    const emptyState = document.createElement("div");

    emptyState.className = "schedule-empty";

    emptyState.innerHTML = `
      <h3>Nothing scheduled today.</h3>
      <p>Things are peaceful.</p>
    `;

    scheduleList.appendChild(emptyState);

    return;
  }

  events.forEach((event) => {
    const item = document.createElement("div");

    item.className = "schedule-item";

    let timeHTML = "";

    if (event.all_day) {
      timeHTML = `
        <strong>ALL</strong>
        <span>DAY</span>
      `;
    } else if (event.start_time) {
      const formattedTime = formatEventTime(event.start_time);
      const timeParts = formattedTime.split(" ");

      timeHTML = `
        <strong>${timeParts[0]}</strong>
        <span>${timeParts[1]}</span>
      `;
    } else {
      timeHTML = `
        <strong>--</strong>
        <span>TIME</span>
      `;
    }

    let detailHTML = "";

    if (event.location) {
      detailHTML = `<p>${event.location}</p>`;
    } else if (event.person && event.person !== "Anyone") {
      detailHTML = `<p>For ${event.person}</p>`;
    } else if (event.all_day) {
      detailHTML = `<p>All-day event</p>`;
    }

    item.innerHTML = `
      <div class="event-time">
        ${timeHTML}
      </div>

      <div class="event-line blue"></div>

      <div class="event-details">
        <h3>${event.title}</h3>
        ${detailHTML}
      </div>
    `;

    scheduleList.appendChild(item);
  });
}

function renderUpcomingEvents(events) {
  const upcomingList = document.querySelector(".upcoming-list");

  if (!upcomingList) {
    return;
  }

  upcomingList.innerHTML = "";

  if (events.length === 0) {
    upcomingList.innerHTML = `
      <div class="upcoming-empty">
        <h3>Nothing coming up.</h3>
        <p>The week ahead is wide open.</p>
      </div>
    `;

    return;
  }

  events.forEach((event) => {
    const eventDate = new Date(`${event.event_date}T00:00:00`);

    const weekday = eventDate
      .toLocaleDateString("en-US", {
        weekday: "short",
      })
      .toUpperCase();

    const day = eventDate.getDate();

    let timeText = "Time not set";

    if (event.all_day) {
      timeText = "All day";
    } else if (event.start_time) {
      timeText = formatEventTime(event.start_time);
    }

    const item = document.createElement("div");

    item.className = "upcoming-item";

    item.innerHTML = `
      <div class="date-block">
        <span>${weekday}</span>
        <strong>${day}</strong>
      </div>

      <div>
        <h3>${event.title}</h3>
        <p>${timeText}</p>
      </div>
    `;

    upcomingList.appendChild(item);
  });
}

function updateTodayEventCount(events) {
  const scheduleCard = document.querySelector(".schedule-card");

  if (!scheduleCard) {
    return;
  }

  const countElement = scheduleCard.querySelector(".card-count");

  if (!countElement) {
    return;
  }

  countElement.textContent = `${events.length} ${
    events.length === 1 ? "event" : "events"
  }`;
}

async function refreshCalendarDashboard() {
  try {
    const response = await fetch("/api/calendar-dashboard");

    if (!response.ok) {
      throw new Error("Calendar dashboard update failed");
    }

    const data = await response.json();

    renderTodayEvents(data.today_events || []);
    renderUpcomingEvents(data.upcoming_events || []);
    updateTodayEventCount(data.today_events || []);
    currentSchedulePage = 0;
    buildSchedulePages();
    renderSchedulePage();
  } catch (error) {
    console.error("Could not refresh calendar dashboard:", error);
  }
}

buildSchedulePages();
renderSchedulePage();

setInterval(moveToNextSchedulePage, SCHEDULE_PAGE_DURATION);

// Refresh live dashboard calendar data
refreshCalendarDashboard();

setInterval(refreshCalendarDashboard, 60 * 1000);

// Refresh tasks

updateDashboardTasks();

setInterval(updateDashboardTasks, 10000);

// Refresh ambient data

const AMBIENT_REFRESH_INTERVAL = 15 * 60 * 1000;

setInterval(() => {
  refreshAmbientData();
}, AMBIENT_REFRESH_INTERVAL);
