# Telegram Bot for Transmission & file control

## Dependencies

* PySocks
* transmission-rpc
* python-telegram-bot

## Installation example

To manage our environment we will use virtualenv. First of all you need to install it and some dependencies.

```
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
sudo apt install python3-venv
```
Copy project to local folder.

```
cd /opt
sudo git clone https://github.com/badretdinov/tg-transmission tgt
```

Configure virtual enviroment and install dependencies.

```
sudo chown your_username:your_group /opt/tgt
cd /opt/tgt
python3 -m venv ENV
source ENV/bin/activate
pip install -r requirements.txt
deactivate
sudo chown root:root /opt/tgt
```
Copy config file and edit it.

```
sudo cp /opt/tgt/example.conf /etc/tgt.conf
sudo nano /etc/tgt.conf
```
Create unit file with next content

```
sudo nano /lib/systemd/system/tgt.service
```
```
[Unit]
Description=Telegram Bot
After=multi-user.target

[Service]
Type=idle
ExecStart=/opt/tgt/ENV/bin/python3 /opt/tgt/bot.py -config /etc/tgt.conf

[Install]
WantedBy=multi-user.target
```
Configure systemd

```
sudo systemctl daemon-reload
sudo systemctl enable tgt.service
sudo systemctl start tgt.service
```
You can check the status of your service using `sudo systemctl status tgt.service`

## Config file

```
{
	"user_whitelist" : "badretdinov",
	"root_dir" : "/media",
	"token" : "telegram-bot-token",
	"rpc" : {
		"address" : "127.0.0.1",
		"port" : 9091,
		"username" : "transmission",
		"password" : "12345678"
	},
	"proxy" : {
		"address" : "192.168.1.1",
		"port" : 1234,
		"username" : "user",
		"password" : "pass"
	}
}
```
* `user_whitelist` - users which allowed to use bot
* `root_dir` - root directory for file browsing. usually is the same as in DLNA server
* `token` - telegram token bot. You can get if from [BotFather](https://telegram.me/botfather)
* `rpc` - transmission rpc server address and credentials
* `proxy` - sock5 proxy address and credentials. Remove this key if you aren't goint to use proxy
