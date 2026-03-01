const API = "http://127.0.0.1:8000";
const rupee = "₹";

/* ================= AUTH ================= */

function register() {
  fetch(API + "/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: username.value,
      password: password.value
    })
  })
  .then(res => {
    if (!res.ok) throw new Error();
    alert("Registered successfully");
    window.location = "login.html";
  })
  .catch(() => alert("User already exists"));
}

function login() {
  fetch(API + "/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: username.value,
      password: password.value
    })
  })
  .then(res => {
    if (!res.ok) throw new Error();
    return res.json();
  })
  .then(data => {
    localStorage.setItem("token", data.token);
    window.location = "dashboard.html";
  })
  .catch(() => alert("Invalid username or password"));
}

function logout() {
  localStorage.removeItem("token");
  window.location = "login.html";
}

/* ================= AUTH HEADER ================= */

function authHeader() {
  return {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + localStorage.getItem("token")
  };
}

/* ================= ADD EXPENSE ================= */

function addExpense() {
  const dt = document.getElementById("expenseDateTime");

  const data = {
    title: title.value,
    category: category.value,
    amount: parseFloat(amount.value)
  };

  // ✅ THIS IS THE FIX
  if (dt && dt.value) {
    // datetime-local → ISO string
    data.created_at = new Date(dt.value).toISOString();
  }

  fetch(API + "/expenses", {
    method: "POST",
    headers: authHeader(),
    body: JSON.stringify(data)
  })
  .then(() => {
    title.value = "";
    category.value = "";
    amount.value = "";
    if (dt) dt.value = "";
    loadExpenses();
  });
}

/* ================= LOAD EXPENSES ================= */

function loadExpenses() {
  fetch(API + "/expenses", {
    headers: authHeader()
  })
  .then(res => res.json())
  .then(data => {
    const body = document.getElementById("expenseTableBody");
    if (!body) return;

    body.innerHTML = "";

    data.forEach(e => {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${e.title}</td>
        <td>${e.category}</td>
        <td>${rupee}${e.amount}</td>
        <td>${new Date(e.created_at).toLocaleString("en-IN")}</td>
        <td>
          <button onclick="editExpense(${e.id}, '${e.title}', '${e.category}', ${e.amount}, '${e.created_at}')">
            Edit
          </button>
          <button onclick="deleteExpense(${e.id})">
            Delete
          </button>
        </td>
      `;

      body.appendChild(tr);
    });
  });
}

/* ================= DELETE ================= */

function deleteExpense(id) {
  if (!confirm("Delete this expense?")) return;

  fetch(API + `/expenses/${id}`, {
    method: "DELETE",
    headers: authHeader()
  })
  .then(() => loadExpenses());
}

/* ================= EDIT ================= */

function editExpense(id, oldTitle, oldCategory, oldAmount, oldDate) {
  const newTitle = prompt("Edit Title", oldTitle);
  if (newTitle === null) return;

  const newCategory = prompt("Edit Category", oldCategory);
  if (newCategory === null) return;

  const newAmount = prompt("Edit Amount", oldAmount);
  if (newAmount === null) return;

  fetch(API + `/expenses/${id}`, {
    method: "PUT",
    headers: authHeader(),
    body: JSON.stringify({
      title: newTitle,
      category: newCategory,
      amount: parseFloat(newAmount),
      created_at: oldDate   // keep original date
    })
  })
  .then(() => loadExpenses());
}

/* ================= SUMMARY ================= */

function getMonthlySummary() {
  const year = document.getElementById("year").value;
  const month = document.getElementById("month").value;

  fetch(API + `/expenses/summary/month-detail/${year}/${month}`, {
    headers: authHeader()
  })
  .then(res => res.json())
  .then(data => {
    let html = `
      <table border="1" width="100%">
        <tr>
          <th>Date</th>
          <th>Time</th>
          <th>Title</th>
          <th>Category</th>
          <th>Amount</th>
        </tr>
    `;

    data.days.forEach(day => {
      day.expenses.forEach((e, i) => {
        html += `
          <tr>
            <td>${i === 0 ? day.date : ""}</td>
            <td>${e.time}</td>
            <td>${e.title}</td>
            <td>${e.category}</td>
            <td>${rupee}${e.amount}</td>
          </tr>
        `;
      });

      html += `
        <tr style="font-weight:bold">
          <td colspan="4">Day Total</td>
          <td>${rupee}${day.day_total}</td>
        </tr>
      `;
    });

    html += `
      <tr style="font-weight:bold">
        <td colspan="4">Month Total</td>
        <td>${rupee}${data.month_total}</td>
      </tr>
    </table>
    `;

    document.getElementById("summaryResult").innerHTML = html;
  });
}

/* ================= AUTO LOAD ================= */

document.addEventListener("DOMContentLoaded", loadExpenses);
