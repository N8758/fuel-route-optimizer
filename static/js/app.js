let map = null;
let routeLayer = null;
let startMarker = null;
let finishMarker = null;
let fuelMarkers = [];


document.addEventListener(
    "DOMContentLoaded",
    function () {

        const form =
            document.getElementById(
                "route-form"
            );

        if (!form) {
            console.error(
                "Route form not found."
            );
            return;
        }

        form.addEventListener(
            "submit",
            handleRouteSubmit
        );
    }
);


/*
 * Handle route form submission
 */
async function handleRouteSubmit(event) {

    event.preventDefault();


    const startInput =
        document.getElementById("start");

    const finishInput =
        document.getElementById("finish");


    const start =
        startInput.value.trim();

    const finish =
        finishInput.value.trim();


    if (!start || !finish) {

        showError(
            "Please enter both start and finish locations."
        );

        return;
    }


    setLoading(true);

    hideError();

    hideResults();


    try {

        const response =
            await fetch(
                "/api/routes/optimize/",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        start: start,
                        finish: finish
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to calculate the route."
            );
        }


        displayResults(data);


    } catch (error) {

        console.error(
            "Route optimization error:",
            error
        );


        showError(
            error.message ||
            "Something went wrong while calculating the route."
        );


    } finally {

        setLoading(false);
    }
}


/*
 * Display API results
 */
function displayResults(data) {

    document
        .getElementById("distance")
        .textContent =
            `${formatNumber(data.distance_miles)} miles`;


    document
        .getElementById("duration")
        .textContent =
            formatDuration(
                data.duration_minutes
            );


    document
        .getElementById("fuel")
        .textContent =
            `${formatNumber(data.total_gallons)} gallons`;


    document
        .getElementById("total-cost")
        .textContent =
            formatCurrency(
                data.total_cost
            );


    displayFuelStops(
        data.fuel_stops || []
    );


    /*
     * IMPORTANT:
     *
     * Make the results section visible BEFORE
     * creating/updating the Leaflet map.
     *
     * Leaflet needs the map container to have
     * a real width and height when it calculates
     * the map size.
     */
    document
        .getElementById("results")
        .classList
        .remove("hidden");


    /*
     * Now display the map.
     */
    displayMap(data);
}


/*
 * Display fuel stops
 */
function displayFuelStops(stops) {

    const container =
        document.getElementById(
            "fuel-stops"
        );


    const count =
        document.getElementById(
            "stop-count"
        );


    count.textContent =
        `${stops.length} ${
            stops.length === 1
                ? "stop"
                : "stops"
        }`;


    container.innerHTML = "";


    if (!stops.length) {

        container.innerHTML = `
            <div class="empty-state">
                No fuel stops were required
                for this route.
            </div>
        `;

        return;
    }


    stops.forEach(
        function (station, index) {

            const stop =
                document.createElement(
                    "div"
                );


            stop.className =
                "fuel-stop";


            const address =
                station.address
                    ? `${station.address}, `
                    : "";


            const distance =
                station.distance_from_start;


            stop.innerHTML = `
                <div class="fuel-stop-header">

                    <div class="fuel-stop-name">
                        ${index + 1}.
                        ${escapeHtml(
                            station.name
                        )}
                    </div>

                    <div class="fuel-price">
                        $${formatNumber(
                            station.price_per_gallon
                        )}/gal
                    </div>

                </div>

                <div class="fuel-stop-details">
                    ${escapeHtml(address)}
                    ${escapeHtml(station.city)},
                    ${escapeHtml(station.state)}
                </div>

                ${
                    distance !== undefined
                    ? `
                        <div class="fuel-stop-distance">
                            ${formatNumber(
                                distance
                            )}
                            miles from start
                        </div>
                    `
                    : ""
                }
            `;


            container.appendChild(stop);
        }
    );
}


/*
 * Display route map
 */
function displayMap(data) {

    const geometry =
        data.geometry;


    /*
     * Validate route geometry.
     */
    if (
        !geometry ||
        !Array.isArray(
            geometry.coordinates
        ) ||
        geometry.coordinates.length < 2
    ) {

        console.error(
            "Invalid route geometry:",
            geometry
        );

        return;
    }


    /*
     * Convert OSRM coordinates:
     *
     * OSRM:
     * [longitude, latitude]
     *
     * Leaflet:
     * [latitude, longitude]
     */
    const coordinates =
        geometry.coordinates
            .filter(
                function (coordinate) {

                    return (
                        Array.isArray(
                            coordinate
                        ) &&
                        coordinate.length >= 2
                    );
                }
            )
            .map(
                function (coordinate) {

                    return [
                        Number(coordinate[1]),
                        Number(coordinate[0])
                    ];
                }
            )
            .filter(
                function (coordinate) {

                    return (
                        Number.isFinite(
                            coordinate[0]
                        ) &&
                        Number.isFinite(
                            coordinate[1]
                        )
                    );
                }
            );


    if (coordinates.length < 2) {

        console.error(
            "Not enough valid coordinates for map."
        );

        return;
    }


    /*
     * Create map once.
     */
    if (!map) {

        map = L.map("map");

        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                attribution:
                    "&copy; OpenStreetMap contributors",

                maxZoom: 19
            }
        ).addTo(map);

    } else {

        clearMapLayers();
    }


    /*
     * IMPORTANT:
     *
     * Tell Leaflet to recalculate the map size.
     *
     * This fixes the issue where the map container
     * was previously hidden.
     */
    map.invalidateSize();


    /*
     * Draw route.
     */
    routeLayer =
        L.polyline(
            coordinates,
            {
                weight: 5
            }
        ).addTo(map);


    /*
     * Start marker.
     */
    const startPoint =
        coordinates[0];


    startMarker =
        L.marker(startPoint)
            .addTo(map)
            .bindPopup(
                `<strong>Start</strong><br>${escapeHtml(
                    data.start
                )}`
            );


    /*
     * Finish marker.
     */
    const finishPoint =
        coordinates[
            coordinates.length - 1
        ];


    finishMarker =
        L.marker(finishPoint)
            .addTo(map)
            .bindPopup(
                `<strong>Finish</strong><br>${escapeHtml(
                    data.finish
                )}`
            );


    /*
     * Add fuel stop markers.
     */
    addFuelStopMarkers(
        data.fuel_stops || []
    );


    /*
     * Fit map to the complete route.
     */
    map.fitBounds(
        routeLayer.getBounds(),
        {
            padding: [30, 30]
        }
    );


    /*
     * Run again after the browser has rendered
     * the results section.
     *
     * This is the important fix for the gray/
     * incorrectly-sized Leaflet map.
     */
    setTimeout(
        function () {

            if (!map || !routeLayer) {
                return;
            }

            map.invalidateSize();

            map.fitBounds(
                routeLayer.getBounds(),
                {
                    padding: [30, 30]
                }
            );

        },
        300
    );
}


/*
 * Add fuel station markers
 */
function addFuelStopMarkers(stops) {

    stops.forEach(
        function (station) {

            /*
             * Backend must provide coordinates.
             */
            if (
                station.latitude === undefined ||
                station.longitude === undefined ||
                station.latitude === null ||
                station.longitude === null
            ) {
                return;
            }


            const latitude =
                Number(
                    station.latitude
                );

            const longitude =
                Number(
                    station.longitude
                );


            if (
                !Number.isFinite(latitude) ||
                !Number.isFinite(longitude)
            ) {
                return;
            }


            const marker =
                L.marker([
                    latitude,
                    longitude
                ])
                    .addTo(map)
                    .bindPopup(
                        `
                        <strong>
                            ${escapeHtml(
                                station.name
                            )}
                        </strong>
                        <br>
                        Fuel:
                        $${formatNumber(
                            station.price_per_gallon
                        )}/gal
                        `
                    );


            fuelMarkers.push(marker);
        }
    );
}


/*
 * Clear existing map layers
 */
function clearMapLayers() {

    if (!map) {
        return;
    }


    if (routeLayer) {

        map.removeLayer(
            routeLayer
        );

        routeLayer = null;
    }


    if (startMarker) {

        map.removeLayer(
            startMarker
        );

        startMarker = null;
    }


    if (finishMarker) {

        map.removeLayer(
            finishMarker
        );

        finishMarker = null;
    }


    fuelMarkers.forEach(
        function (marker) {

            map.removeLayer(marker);
        }
    );


    fuelMarkers = [];
}


/*
 * Loading state
 */
function setLoading(isLoading) {

    const button =
        document.getElementById(
            "optimize-button"
        );


    const loading =
        document.getElementById(
            "loading"
        );


    if (isLoading) {

        button.disabled = true;

        button.textContent =
            "Calculating...";

        loading.classList
            .remove("hidden");

    } else {

        button.disabled = false;

        button.textContent =
            "Optimize Route";

        loading.classList
            .add("hidden");
    }
}


/*
 * Show error
 */
function showError(message) {

    const errorElement =
        document.getElementById(
            "error-message"
        );


    errorElement.textContent =
        message;


    errorElement.classList
        .remove("hidden");
}


/*
 * Hide error
 */
function hideError() {

    document
        .getElementById(
            "error-message"
        )
        .classList
        .add("hidden");
}


/*
 * Hide results
 */
function hideResults() {

    document
        .getElementById(
            "results"
        )
        .classList
        .add("hidden");
}


/*
 * Format numbers
 */
function formatNumber(value) {

    if (
        value === null ||
        value === undefined ||
        Number.isNaN(Number(value))
    ) {

        return "-";
    }


    return Number(value)
        .toLocaleString(
            "en-US",
            {
                maximumFractionDigits: 2
            }
        );
}


/*
 * Format currency
 */
function formatCurrency(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "N/A";
    }


    return Number(value)
        .toLocaleString(
            "en-US",
            {
                style: "currency",
                currency: "USD"
            }
        );
}


/*
 * Format duration
 */
function formatDuration(minutes) {

    if (
        minutes === null ||
        minutes === undefined
    ) {

        return "-";
    }


    const totalMinutes =
        Math.round(
            Number(minutes)
        );


    const hours =
        Math.floor(
            totalMinutes / 60
        );


    const remainingMinutes =
        totalMinutes % 60;


    if (hours === 0) {

        return `${remainingMinutes} min`;
    }


    return `${hours}h ${remainingMinutes}m`;
}


/*
 * Prevent HTML injection when displaying
 * station names and addresses.
 */
function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";
    }


    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}