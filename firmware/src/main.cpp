#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32httpUpdate.h>

#define CURRENT_VERSION 1
#define FIRMWARE_SERVER_IP "192.168.1.21:5000"
#define UPDATE_PATH "/update"

String wifiSSID = "Griya Ilham";
String wifiPassword = "Siput_Ngebut";

// Declaration of Functions
void connectWifi();
void checkUpdate();
t_httpUpdate_return updateFirmware(String url_update);

void setup()
{
  Serial.begin(9600);
  connectWifi();
}

void loop()
{
  checkUpdate();
  delay(1000);
}

void checkUpdate() {
  Serial.println("\n\n-----------------------------------------------------");
  Serial.println("Checking Update...");

  // Build the update URL with parameters
  String url = "http://" + String(FIRMWARE_SERVER_IP) + String(UPDATE_PATH) +
               "?mac_address=" + WiFi.macAddress();

  HTTPClient http;
  String response;
  http.begin(url);
  int httpCode = http.GET();

  if(httpCode > 0) {
    response = http.getString();
    Serial.println("Response from Server: " + response);

    StaticJsonDocument<1024> doc;
    deserializeJson(doc, response);
    JsonObject obj = doc.as<JsonObject>();

    String version = obj[String("version")];
    String url_update = obj[String("url")];

    Serial.println("Version: " + version);
    Serial.println("URL: " + url_update);

    String server_version = url_update.substring(url_update.lastIndexOf('_') + 1);
    if (server_version.toInt() > CURRENT_VERSION) {
      Serial.println("Update Available");
      if(updateFirmware(url_update) == HTTP_UPDATE_OK) {
        Serial.println("Update Success");
        ESP.restart();
      } else {
        Serial.println("Update Failed");
      }
    } else {
      Serial.println("No Update Available");
      Serial.println("-----------------------------------------------------\n\n");
    }
  } else {
    Serial.println("HTTP request failed");
  }

  http.end();
}

t_httpUpdate_return updateFirmware(String url_update)
{
  t_httpUpdate_return ret;

  if(WiFi.status()==WL_CONNECTED){
    
    ret= ESPhttpUpdate.update(url_update);

    switch(ret)
    {
      case HTTP_UPDATE_FAILED:
        Serial.println("[update] Update failed.");
        return ret;
        break;

      case HTTP_UPDATE_NO_UPDATES:
        Serial.println("[update] No update.");
        return ret;
        break;

      case HTTP_UPDATE_OK:
        Serial.println("[update] Update OK.");
        break;
    }
  }
}

void connectWifi()
{
  Serial.println("Connecting to Wifi\n");
  WiFi.begin(wifiSSID.c_str(), wifiPassword.c_str());
  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.print(".");
    delay(500);
  }

  Serial.println("Wifi Connected");
  Serial.println(WiFi.SSID());
  Serial.println(WiFi.RSSI());
  Serial.println(WiFi.macAddress());
  Serial.println(WiFi.localIP());
  Serial.println(WiFi.gatewayIP());
  Serial.println(WiFi.dnsIP());
}
