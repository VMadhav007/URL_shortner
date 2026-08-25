const form = document.getElementById("url-form");

const originalUrlInput = document.getElementById("original-url");
const customCodeInput = document.getElementById("custom-code");
const expirationInput = document.getElementById("expiration");

const result = document.getElementById("result");
const shortUrl = document.getElementById("short-url");
const resultOriginalUrl = document.getElementById("result-original-url");
const openButton = document.getElementById("open-button");

const error = document.getElementById("error");
const copyButton = document.getElementById("copy-button");


form.addEventListener("submit", async (event) => {

    event.preventDefault();

    // Hide old messages
    result.classList.add("hidden");
    error.classList.add("hidden");

    const originalUrl = originalUrlInput.value;
    const customCode = customCodeInput.value.trim();
    const expiration = expirationInput.value;

    const requestBody = {
        original_url: originalUrl
    };

    // Only send custom_code if user entered one
    if (customCode) {
        requestBody.custom_code = customCode;
    }

    if (expiration) {
        requestBody.expires_in = parseInt(expiration, 10);
    }

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/urls",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(requestBody)
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to shorten URL"
            );
        }

        // Display the generated short URL and other details
        shortUrl.textContent = data.short_url;
        shortUrl.href = data.short_url;
        
        resultOriginalUrl.textContent = originalUrl;
        openButton.href = data.short_url;

        result.classList.remove("hidden");

    } catch (err) {

        error.textContent = err.message;
        error.classList.remove("hidden");
    }
});


copyButton.addEventListener("click", async () => {

    await navigator.clipboard.writeText(
        shortUrl.textContent
    );

    copyButton.textContent = "Copied!";

    setTimeout(() => {
        copyButton.textContent = "Copy";
    }, 1500);
});