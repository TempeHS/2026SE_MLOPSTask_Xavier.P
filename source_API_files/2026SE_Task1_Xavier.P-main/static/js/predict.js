document
  .getElementById("predict-form")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const form = e.target;
    const data = {};
    new FormData(form).forEach((val, key) => {
      if (key !== "csrf_token") data[key] = parseFloat(val);
    });

    console.log("Sending data:", data);

    try {
      const res = await fetch("/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      console.log("Response status:", res.status);
      const json = await res.json();
      console.log("Response JSON:", json);

      const results = document.getElementById("results");
      const errorBox = document.getElementById("error-box");

      if (json.error) {
        errorBox.classList.remove("hidden");
        errorBox.textContent = json.error;
        results.classList.add("hidden");
      } else {
        results.classList.remove("hidden");
        errorBox.classList.add("hidden");
        document.getElementById("prediction-value").textContent =
          json.prediction;
      }
    } catch (err) {
      console.error("Fetch error:", err);
      const errorBox = document.getElementById("error-box");
      errorBox.classList.remove("hidden");
      errorBox.textContent = "Request failed: " + err.message;
    }
  });
