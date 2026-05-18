// 👉 Redirect from search page to results page
function goToResults() {
    const location    = document.getElementById("location").value;
    const destination = document.getElementById("destination").value.trim();
    const days        = document.getElementById("days").value;
    const budget      = document.getElementById("budget").value;
    const dateLabel   = document.getElementById("dateLabel")?.textContent;
    const travelDate  = (dateLabel && dateLabel !== "Travel Date") ? dateLabel : "";

    if (!location || !destination || !travelDate || !days || !budget) {
        alert("Please fill in all fields including travel date!");
        return;
    }

   const email = localStorage.getItem("userEmail");

    localStorage.removeItem("location");
    localStorage.removeItem("destination");
    localStorage.removeItem("travelDate");
    localStorage.removeItem("days");
    localStorage.removeItem("budget");

    if (email) {
        localStorage.setItem("userEmail", email);
    }
    localStorage.setItem("location", location);
    localStorage.setItem("destination", destination);
    localStorage.setItem("travelDate", travelDate);
    localStorage.setItem("days", days);
    localStorage.setItem("budget", budget);

    // Redirect
    window.location.href = "/result";
}

// 👉 Load results when result.html opens
window.onload = async function () {

    // Run ONLY on result page
    if (window.location.pathname.includes("/result")) {

        const location    = localStorage.getItem("location");
        const destination  = localStorage.getItem("destination");
        const travelDate   = localStorage.getItem("travelDate") || "";
        const days         = localStorage.getItem("days");
        const budget       = localStorage.getItem("budget");


        // Safety check — if someone opens result.html directly
        if (!location || !destination || !days || !budget) {
            document.getElementById("result").innerHTML =
                "<p style='text-align:center;'>No trip data found. <a href='index.html'>Go back</a></p>";
            return;
        }

         
        // 👉 Set background image dynamically based on destination
        // Converts destination to lowercase and removes spaces: "Manali" → "manali"
        const imageName = destination.toLowerCase().replace(/\s+/g, "");
        const extensions = ["jpeg", "jpg", "png", "webp"];

        // Try each extension until one loads
        function trySetBackground(index) {
            if (index >= extensions.length) {
                // Fallback: keep the existing CSS background (bg2.jpeg)
                console.warn("No destination image found for:", imageName);
                return;
            }
            const img = new Image();
            const src = `/static/${imageName}.${extensions[index]}`;
            img.onload = () => {
                document.body.style.backgroundImage = `url('${src}')`;
            };
            img.onerror = () => trySetBackground(index + 1);
            img.src = src;
        }
        trySetBackground(0);

        try {
            const response = await fetch("http://127.0.0.1:5000/plan", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ location, destination, days, budget })
            });

            const data = await response.json();

            let output = `
            <div class="result-container">

                <div class="glass-panel trip-header">
                    <h2>${data.trip.destination}</h2>
                    <p>${data.trip.days} Days • Budget ₹${data.trip.budget} • ${travelDate ? " • 📅 " + travelDate : ""}</p>
                </div>

                <div class="glass-panel">
                    <div class="section-title">📅 Itinerary</div>
            `;

            data.trip.itinerary.forEach(day => {
                let activitiesHTML = "";
                if (Array.isArray(day.plan)) {
                    day.plan.forEach(slot => {
                        activitiesHTML += `
                            <div class="activity-row">
                                <span class="time-badge">${slot.time}</span>
                                <div class="activity-info">
                                    <strong>${slot.activity}</strong>
                                    <p>${slot.description}</p>
                                </div>
                                <span class="activity-cost">₹${slot.cost}</span>
                            </div>
                        `;
                    });
                } else {
                    activitiesHTML = `<p>${day.plan}</p>`;
                }

                output += `
                    <div class="day-card">
                        <h4>Day ${day.day}</h4>
                        ${activitiesHTML}
                    </div>
                `;
            });

            output += `
                </div>

                <div class="glass-panel">
                    <div class="section-title">🚗 Transport Options</div>
            `;

            data.transport.forEach(option => {
                if (option.available === false) {
                    output += `
                        <div class="transport-card unavailable">
                            <div>
                                <h4>${option.type}</h4>
                                <p>Not Available</p>
                            </div>
                            <button disabled style="background:#ccc;cursor:not-allowed;">N/A</button>
                        </div>
                    `;
                } else {
                    output += `
                        <div class="transport-card">
                            <div>
                                <h4>${option.type}</h4>
                                <p>₹${option.price} • ${option.time}</p>
                            </div>
                            <button onclick="book('${option.type}', ${option.price})">Book</button>
                        </div>
                    `;
                }
            });

            output += `</div></div>`;

            document.getElementById("result").innerHTML = output;
            
        } catch (error) {
            document.getElementById("result").innerHTML =
                "<p style='text-align:center;'>Error loading trip data. Make sure backend is running.</p>";
        }
    }
};


// 👉 Transport booking → payment gateway
function book(type, price) {

    const destination = localStorage.getItem("destination") || "";
    const travelDate  = localStorage.getItem("travelDate") || "";

    localStorage.setItem("selected_transport", JSON.stringify({
        type: type,
        price: price,
        destination: destination,
        travelDate: travelDate
    }));

    window.location.href = "/transport_booking";
}
function showSignup() {
    document.querySelector(".login-panel").style.display = "none";
    document.querySelector(".signup-panel").style.display = "block";
}

function showLogin() {
    document.querySelector(".signup-panel").style.display = "none";
    document.querySelector(".login-panel").style.display = "block";
}

function moveIndicator() {
    const active = document.querySelector(".navbar-links a.active");
    const nav = document.querySelector(".navbar-links");

    if (!active || !nav) return;

    const rect = active.getBoundingClientRect();
    const parentRect = nav.getBoundingClientRect();

    const left = rect.left - parentRect.left;
    const width = rect.width;

    nav.style.setProperty("--indicator-left", `${left}px`);
    nav.style.setProperty("--indicator-width", `${width}px`);

    nav.style.position = "relative";

    nav.style.setProperty("--indicator-visible", "1");

    nav.style.setProperty("--indicator-height", "2px");

    nav.style.setProperty("--indicator-bottom", "6px");

    nav.style.setProperty("--indicator-glow", "1");

    nav.style.setProperty("--indicator-opacity", "1");

    nav.style.setProperty("--indicator-scale", "1");

    nav.style.setProperty("--indicator-radius", "2px");

    nav.style.setProperty("--indicator-transition", "0.35s ease");

    nav.style.setProperty("--indicator-bg", "white");

    nav.style.setProperty("--indicator-shadow",
        "0 0 8px rgba(255,255,255,0.9), 0 0 16px rgba(255,255,255,0.6)"
    );

    nav.style.setProperty("--indicator-transform", "translateX(0)");
}

window.addEventListener("load", moveIndicator);
window.addEventListener("resize", moveIndicator);

function logout() {
    localStorage.clear()
    window.location.href = "/"; // go back to login page
}
// Fade in on page load
document.addEventListener("DOMContentLoaded", () => {
    document.body.classList.add("fade-in");

    requestAnimationFrame(() => {
        document.body.classList.remove("fade-in");
    });
});

// Fade out on navigation
document.querySelectorAll("a").forEach(link => {
    const url = link.getAttribute("href");

    // only internal links
    if (url && url.startsWith("/")) {
        link.addEventListener("click", function(e) {
            e.preventDefault();

            document.body.classList.add("fade-out");

            setTimeout(() => {
                window.location.href = url;
            }, 300);
        });
    }
});

function scrollHotels(direction) {
    const container = document.getElementById("hotelsGrid");
    const scrollAmount = 300; // adjust for speed

    container.scrollBy({
        left: direction * scrollAmount,
        behavior: "smooth"
    });
}

function bookHotel(name, location, price) {

    const email = localStorage.getItem("userEmail");

    if (!email) {
        alert("Please login first!");
        return;
    }

    // Strip ₹ and commas to get numeric value
    const cleanPrice = parseInt(String(price).replace("₹","").replace(/,/g,"").trim()) || 0;

    localStorage.setItem("planora_payment", JSON.stringify({
        title:    "🏨 " + name,
        subtitle: "📍 " + location,
        amount:   cleanPrice,
        type:     "hotel",
        origin:   "/hotel",
        extra: {
            hotel:    name,
            location: location,
            price:    cleanPrice
        }
    }));

    window.location.href = "/payment";
}