import React, { useState, useEffect } from 'react';
import {
  StatusBar,
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Image,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

// ВАЖНО: Получите бесплатный API ключ на https://openweathermap.org/api
const API_KEY = '757b2eaa1fe0991372cbe8789c1362cf';
const BASE_URL = 'https://api.openweathermap.org/data/2.5';

export default function App() {
  const [city, setCity] = useState('');
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const saved = await AsyncStorage.getItem('favorites');
      if (saved) {
        setFavorites(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Ошибка загрузки избранного:', error);
    }
  };

  const saveFavorites = async (newFavorites) => {
    try {
      await AsyncStorage.setItem('favorites', JSON.stringify(newFavorites));
      setFavorites(newFavorites);
    } catch (error) {
      console.error('Ошибка сохранения:', error);
    }
  };

  const fetchWeather = async (searchCity) => {
    if (!searchCity.trim()) {
      Alert.alert('Ошибка', 'Введите название города');
      return;
    }

    if (API_KEY === 'YOUR_API_KEY_HERE') {
      Alert.alert(
        'Нужен API ключ',
        'Получите бесплатный ключ на openweathermap.org и вставьте в App.js'
      );
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(
        `${BASE_URL}/weather?q=${searchCity}&appid=${API_KEY}&units=metric&lang=ru`
      );
      setWeather(response.data);
    } catch (error) {
      Alert.alert('Ошибка', 'Город не найден');
    }
    setLoading(false);
  };

  const addToFavorites = () => {
    if (weather && !favorites.includes(weather.name)) {
      const newFavorites = [...favorites, weather.name];
      saveFavorites(newFavorites);
      Alert.alert('Добавлено', `${weather.name} добавлен в избранное`);
    }
  };

  const removeFromFavorites = (cityName) => {
    const newFavorites = favorites.filter((f) => f !== cityName);
    saveFavorites(newFavorites);
  };

  const getWeatherIcon = (iconCode) => {
    return `https://openweathermap.org/img/wn/${iconCode}@4x.png`;
  };

  const getGradientColors = () => {
    if (!weather) return ['#667eea', '#764ba2'];

    const temp = weather.main.temp;
    if (temp < 0) return ['#74ebd5', '#ACB6E5'];
    if (temp < 10) return ['#89f7fe', '#66a6ff'];
    if (temp < 20) return ['#667eea', '#764ba2'];
    if (temp < 30) return ['#f093fb', '#f5576c'];
    return ['#ff9a9e', '#fecfef'];
  };

  return (
    <LinearGradient colors={getGradientColors()} style={styles.container}>
      <StatusBar style="light" />

      <View style={styles.header}>
        <Text style={styles.title}>Погода</Text>
      </View>

      <View style={styles.searchContainer}>
        <TextInput
          style={styles.input}
          placeholder="Введите город..."
          placeholderTextColor="rgba(255,255,255,0.7)"
          value={city}
          onChangeText={setCity}
          onSubmitEditing={() => fetchWeather(city)}
        />
        <TouchableOpacity
          style={styles.searchButton}
          onPress={() => fetchWeather(city)}
        >
          <Text style={styles.searchButtonText}>Найти</Text>
        </TouchableOpacity>
      </View>

      {loading && (
        <ActivityIndicator size="large" color="#fff" style={styles.loader} />
      )}

      {weather && !loading && (
        <View style={styles.weatherCard}>
          <Text style={styles.cityName}>{weather.name}, {weather.sys.country}</Text>

          <Image
            source={{ uri: getWeatherIcon(weather.weather[0].icon) }}
            style={styles.weatherIcon}
          />

          <Text style={styles.temperature}>
            {Math.round(weather.main.temp)}°C
          </Text>

          <Text style={styles.description}>
            {weather.weather[0].description}
          </Text>

          <View style={styles.detailsContainer}>
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>Ощущается</Text>
              <Text style={styles.detailValue}>
                {Math.round(weather.main.feels_like)}°C
              </Text>
            </View>
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>Влажность</Text>
              <Text style={styles.detailValue}>{weather.main.humidity}%</Text>
            </View>
            <View style={styles.detailItem}>
              <Text style={styles.detailLabel}>Ветер</Text>
              <Text style={styles.detailValue}>{weather.wind.speed} м/с</Text>
            </View>
          </View>

          <TouchableOpacity
            style={styles.favoriteButton}
            onPress={addToFavorites}
          >
            <Text style={styles.favoriteButtonText}>
              {favorites.includes(weather.name) ? '★ В избранном' : '☆ В избранное'}
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {favorites.length > 0 && (
        <View style={styles.favoritesContainer}>
          <Text style={styles.favoritesTitle}>Избранные города</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {favorites.map((favCity, index) => (
              <TouchableOpacity
                key={index}
                style={styles.favoriteCity}
                onPress={() => fetchWeather(favCity)}
                onLongPress={() => {
                  Alert.alert(
                    'Удалить город?',
                    `Удалить ${favCity} из избранного?`,
                    [
                      { text: 'Отмена', style: 'cancel' },
                      { text: 'Удалить', onPress: () => removeFromFavorites(favCity) },
                    ]
                  );
                }}
              >
                <Text style={styles.favoriteCityText}>{favCity}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 50,
  },
  header: {
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 3,
  },
  searchContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  input: {
    flex: 1,
    height: 50,
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 25,
    paddingHorizontal: 20,
    fontSize: 16,
    color: '#fff',
    marginRight: 10,
  },
  searchButton: {
    height: 50,
    paddingHorizontal: 25,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  loader: {
    marginTop: 50,
  },
  weatherCard: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    marginHorizontal: 20,
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
  },
  cityName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  weatherIcon: {
    width: 120,
    height: 120,
  },
  temperature: {
    fontSize: 64,
    fontWeight: '200',
    color: '#fff',
  },
  description: {
    fontSize: 20,
    color: '#fff',
    textTransform: 'capitalize',
    marginBottom: 20,
  },
  detailsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: 20,
  },
  detailItem: {
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
  },
  detailValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  favoriteButton: {
    backgroundColor: 'rgba(255,255,255,0.3)',
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 25,
  },
  favoriteButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  favoritesContainer: {
    marginTop: 20,
    paddingHorizontal: 20,
  },
  favoritesTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 10,
  },
  favoriteCity: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 10,
  },
  favoriteCityText: {
    color: '#fff',
    fontSize: 14,
  },
});
