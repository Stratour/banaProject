console.log("GLOBAL address_autocomplete.js LOADED");

function setupAutocomplete(inputId, hiddenId, suggestionListId) {
    const inputField = document.getElementById(inputId);
    const hiddenField = document.getElementById(hiddenId);
    const suggestionList = document.getElementById(suggestionListId);

    console.log("setupAutocomplete init:", { inputId, hiddenId, suggestionListId });
    console.log("inputField:", inputField);
    console.log("hiddenField:", hiddenField);
    console.log("suggestionList:", suggestionList);

    if (!inputField || !suggestionList) return;

    const favoriteDataElement = document.getElementById("favorite-addresses-data");
    const favoriteAddresses = favoriteDataElement
        ? JSON.parse(favoriteDataElement.textContent)
        : [];

    const clearSuggestions = () => {
        suggestionList.innerHTML = "";
    };

    const renderFavorites = () => {
        clearSuggestions();

        if (!favoriteAddresses.length) return;

        favoriteAddresses.forEach(addr => {
            const li = document.createElement("li");
            li.classList.add(
                "cursor-pointer",
                "p-2",
                "hover:bg-gray-100",
                "border-b"
            );

            li.innerHTML = `
                <div class="text-sm font-semibold text-gray-900">${addr.label}</div>
                <div class="text-xs text-gray-500">${addr.address}</div>
            `;

            li.addEventListener("click", () => {
                inputField.value = addr.address || "";

                if (hiddenField) {
                    hiddenField.value = addr.place_id || "";
                    console.log("Favorite selected place_id:", hiddenField.value);
                }

                clearSuggestions();
            });

            suggestionList.appendChild(li);
        });
    };

    inputField.addEventListener("focus", () => {
        if (inputField.value.trim().length < 3) {
            renderFavorites();
        }
    });

    inputField.addEventListener("input", async () => {
        const query = inputField.value.trim();

        if (hiddenField) {
            hiddenField.value = "";
        }

        if (query.length < 3) {
            renderFavorites();
            return;
        }

        try {
            const url = `/trajets/autocomplete/?query=${ encodeURIComponent(query)}`;
        console.log("FETCH URL:", url);

        const response = await fetch(url, {
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        });

        console.log("FETCH STATUS:", response.status);

        const data = await response.json();
        console.log("AUTOCOMPLETE RESPONSE:", data);

        clearSuggestions();

        (data.suggestions || []).forEach(s => {
            const li = document.createElement("li");
            li.textContent = s.description || "";

            li.classList.add(
                "cursor-pointer",
                "p-2",
                "hover:bg-gray-100",
                "border-b"
            );

            li.addEventListener("click", () => {
                inputField.value = s.description || "";

                if (hiddenField) {
                    hiddenField.value = s.place_id || "";
                    console.log("Autocomplete selected place_id:", hiddenField.value);
                }

                clearSuggestions();
            });

            suggestionList.appendChild(li);
        });

    } catch (err) {
        console.error("Autocomplete error:", err);
    }
});

document.addEventListener("click", (event) => {
    const clickedInside =
        inputField.contains(event.target) ||
        suggestionList.contains(event.target);

    if (!clickedInside) {
        clearSuggestions();
    }
});
}