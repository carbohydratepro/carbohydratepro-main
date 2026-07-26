"use strict";
const weatherLabels = {
    0: '快晴',
    1: '晴れ',
    2: '一部くもり',
    3: 'くもり',
    45: '霧',
    48: '霧氷',
    51: '弱い霧雨',
    53: '霧雨',
    55: '強い霧雨',
    61: '弱い雨',
    63: '雨',
    65: '強い雨',
    71: '弱い雪',
    73: '雪',
    75: '強い雪',
    80: '弱いにわか雨',
    81: 'にわか雨',
    82: '強いにわか雨',
    95: '雷雨',
};
const displayWeather = async (latitude, longitude, status) => {
    var _a, _b, _c, _d, _e;
    const params = new URLSearchParams({
        latitude: String(latitude),
        longitude: String(longitude),
        current: 'temperature_2m,apparent_temperature,weather_code',
        daily: 'temperature_2m_max,temperature_2m_min,precipitation_probability_max',
        timezone: 'auto',
        forecast_days: '1',
    });
    const response = await fetch(`https://api.open-meteo.com/v1/forecast?${params.toString()}`);
    if (!response.ok)
        throw new Error(`weather status ${response.status}`);
    const weather = await response.json();
    const current = weather.current;
    const daily = weather.daily;
    if (typeof (current === null || current === void 0 ? void 0 : current.temperature_2m) !== 'number')
        throw new Error('weather data missing');
    const label = (_b = weatherLabels[(_a = current.weather_code) !== null && _a !== void 0 ? _a : -1]) !== null && _b !== void 0 ? _b : '天気情報';
    const maximum = (_c = daily === null || daily === void 0 ? void 0 : daily.temperature_2m_max) === null || _c === void 0 ? void 0 : _c[0];
    const minimum = (_d = daily === null || daily === void 0 ? void 0 : daily.temperature_2m_min) === null || _d === void 0 ? void 0 : _d[0];
    const rain = (_e = daily === null || daily === void 0 ? void 0 : daily.precipitation_probability_max) === null || _e === void 0 ? void 0 : _e[0];
    const ranges = typeof maximum === 'number' && typeof minimum === 'number'
        ? `最高${Math.round(maximum)}℃／最低${Math.round(minimum)}℃`
        : '';
    const rainText = typeof rain === 'number' ? `降水${Math.round(rain)}%` : '';
    status.textContent = `${label} ${Math.round(current.temperature_2m)}℃ ${ranges} ${rainText}`.trim();
};
document.addEventListener('DOMContentLoaded', () => {
    const panel = document.querySelector('[data-weather-panel]');
    const status = panel === null || panel === void 0 ? void 0 : panel.querySelector('[data-weather-status]');
    const button = panel === null || panel === void 0 ? void 0 : panel.querySelector('[data-weather-load]');
    if (!panel || !status || !button)
        return;
    button.addEventListener('click', () => {
        if (!navigator.geolocation) {
            status.textContent = 'このブラウザでは位置情報を利用できません。';
            return;
        }
        button.disabled = true;
        status.textContent = '現在地の天気を取得しています…';
        navigator.geolocation.getCurrentPosition((position) => {
            displayWeather(position.coords.latitude, position.coords.longitude, status)
                .then(() => { button.disabled = false; })
                .catch(() => {
                status.textContent = '天気を取得できませんでした。';
                button.disabled = false;
            });
        }, () => {
            status.textContent = '位置情報が許可されなかったため取得しませんでした。';
            button.disabled = false;
        }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 });
    });
});
