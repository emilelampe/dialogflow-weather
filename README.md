# Dialogflow CX Weather Forecast chatbot

This is the webhook for a chatbot that can give you the weather forecast of today or one of the coming 6 days. It provides you with the minimum and maximum forecasted temperature. The chatbot is created with Dialogflow CX. The app makes API calls through Flask. ngrok is used for deployment. Both can be ran with tmux on an EC2 instance.

## APIs

For the weather forecasting, it makes use of the Open-Meteo forecast API. This one is chosen because it is free and provides a forecast of 7 days (including the current day). The API requires a longitude and latitude, so it also makes use of OpenWeatherMap's API for converting city names into coordinates.