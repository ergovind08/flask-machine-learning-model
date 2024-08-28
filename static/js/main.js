document.addEventListener("DOMContentLoaded", function () {
  const cuisineSelect = document.getElementById("cuisine-select");
  const cuisineInput = document.getElementById("cuisine-input");
  const ratingSelect = document.getElementById("rating-select");
  const vegSelect = document.getElementById("veg-select");
  const orderSelect = document.getElementById("order-select");
  const recommendBtn = document.getElementById("recommend-btn");
  const recommendationsDiv = document.getElementById("recommendations");

  // Fetch cuisines and populate dropdown
  fetch("/cuisines")
    .then((response) => {
      if (!response.ok)
        throw new Error("Network response was not ok " + response.statusText);
      return response.json();
    })
    .then((cuisines) => {
      cuisines.forEach((cuisine) => {
        const option = document.createElement("option");
        option.value = cuisine;
        option.textContent = cuisine;
        cuisineSelect.appendChild(option);
      });
    })
    .catch((error) => {
      console.error("Error fetching cuisines:", error);
      cuisineSelect.innerHTML = "<option>Error loading cuisines</option>";
    });

  // Set rating options
  [1, 2, 3, 4].forEach((rating) => {
    const option = document.createElement("option");
    option.value = rating;
    option.textContent = rating;
    ratingSelect.appendChild(option);
  });

  // Set veg options
  ["Yes", "No", "Both"].forEach((veg) => {
    const option = document.createElement("option");
    option.value = veg;
    option.textContent = veg;
    vegSelect.appendChild(option);
  });

  // Set order options
  ["Seating", "Order"].forEach((order) => {
    const option = document.createElement("option");
    option.value = order;
    option.textContent = order;
    orderSelect.appendChild(option);
  });

  // Handle recommend button click
  recommendBtn.addEventListener("click", () => {
    // Collect form data
    const selectedCuisine = cuisineInput.value.trim() || cuisineSelect.value;
    const budget = document.getElementById("budget").value;
    const rating = ratingSelect.value;
    const vegChoice = vegSelect.value;
    const orderChoice = orderSelect.value;

    // Prepare request data
    const requestData = {
      preferred_cuisines: [selectedCuisine],
      budget: budget,
      min_rating: rating,
      veg_choice: vegChoice,
      order_choice: orderChoice,
    };

    console.log("Sending request with data:", requestData);

    // Send POST request
    fetch("/recommend", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestData),
    })
      .then((response) => {
        console.log("Response status:", response.status);
        if (!response.ok) {
          return response.json().then((errorData) => {
            throw new Error(errorData.error || "Unknown error");
          });
        }
        return response.json();
      })
      .then((recommendations) => {
        console.log("Received recommendations:", recommendations);
        recommendationsDiv.innerHTML = "";
        if (recommendations && recommendations.length > 0) {
          recommendations.forEach((restaurant) => {
            const div = document.createElement("div");
            div.className = "restaurant";
            div.innerHTML = `
              <h2>${restaurant.Name}</h2>
              <p><strong>Location:</strong> ${restaurant.Full_Address}</p>
              <p><strong>Average Cost:</strong> ${restaurant.AverageCost}</p>
              <p><strong>Cuisines:</strong> ${restaurant.Cuisines}</p>
              <a href="${restaurant.URL}" class="order-button" target="_blank">Order Now &rarr;</a>
            `;
            recommendationsDiv.appendChild(div);
          });
        } else {
          recommendationsDiv.innerHTML = "<p>No recommendations found.</p>";
        }
      })
      .catch((error) => {
        console.error("Error fetching recommendations:", error);
        recommendationsDiv.innerHTML = `<p>Error fetching recommendations: ${error.message}</p>`;
      });
  });
});
