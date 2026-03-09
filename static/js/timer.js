let time = 30;

let interval = setInterval(() => {
    document.getElementById("time").innerText = time;
    time--;

    if (time < 0) {
        clearInterval(interval);
        document.getElementById("form").submit();
    }
}, 1000);
