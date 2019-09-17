# Client, server, and arduino code to control a DC </br>
# motor connected to an esp8266 board

### client/
* handles end-user connection to app
* routes requests
* defines API to communicate b/t web and board
* serves HMTL/CSS

### server
* handles user authentification and authorization
* defines connection to and operations on motor

### sketches
* testing echo server for esp8266
* DC motor and API setup for esp8266
* DC motor setup on mega2560