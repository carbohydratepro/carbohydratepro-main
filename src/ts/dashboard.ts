interface WeatherApiResponse {
  current?: {
    temperature_2m?: number;
    apparent_temperature?: number;
    weather_code?: number;
  };
  daily?: {
    temperature_2m_max?: number[];
    temperature_2m_min?: number[];
    precipitation_probability_max?: number[];
  };
}

const weatherLabels: Record<number, string> = {
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

const displayWeather = async (latitude: number, longitude: number, status: HTMLElement): Promise<void> => {
  const params = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
    current: 'temperature_2m,apparent_temperature,weather_code',
    daily: 'temperature_2m_max,temperature_2m_min,precipitation_probability_max',
    timezone: 'auto',
    forecast_days: '1',
  });
  const response = await fetch(`https://api.open-meteo.com/v1/forecast?${params.toString()}`);
  if (!response.ok) throw new Error(`weather status ${response.status}`);
  const weather = await response.json() as WeatherApiResponse;
  const current = weather.current;
  const daily = weather.daily;
  if (typeof current?.temperature_2m !== 'number') throw new Error('weather data missing');

  const label = weatherLabels[current.weather_code ?? -1] ?? '天気情報';
  const maximum = daily?.temperature_2m_max?.[0];
  const minimum = daily?.temperature_2m_min?.[0];
  const rain = daily?.precipitation_probability_max?.[0];
  const ranges = typeof maximum === 'number' && typeof minimum === 'number'
    ? `最高${Math.round(maximum)}℃／最低${Math.round(minimum)}℃`
    : '';
  const rainText = typeof rain === 'number' ? `降水${Math.round(rain)}%` : '';
  status.textContent = `${label} ${Math.round(current.temperature_2m)}℃ ${ranges} ${rainText}`.trim();
};

document.addEventListener('DOMContentLoaded', () => {
  const panel = document.querySelector<HTMLElement>('[data-weather-panel]');
  const status = panel?.querySelector<HTMLElement>('[data-weather-status]');
  const button = panel?.querySelector<HTMLButtonElement>('[data-weather-load]');
  if (!panel || !status || !button) return;

  button.addEventListener('click', () => {
    if (!navigator.geolocation) {
      status.textContent = 'このブラウザでは位置情報を利用できません。';
      return;
    }
    button.disabled = true;
    status.textContent = '現在地の天気を取得しています…';
    navigator.geolocation.getCurrentPosition(
      (position) => {
        displayWeather(position.coords.latitude, position.coords.longitude, status)
          .then(() => { button.disabled = false; })
          .catch(() => {
            status.textContent = '天気を取得できませんでした。';
            button.disabled = false;
          });
      },
      () => {
        status.textContent = '位置情報が許可されなかったため取得しませんでした。';
        button.disabled = false;
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 },
    );
  });
});
