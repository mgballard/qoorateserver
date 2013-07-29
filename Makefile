#
# Just some basic functionality to manage our server

start:
	echo "Starting Qoorate"
	./start-server $(CURDIR)

stop:
	echo "Stopping Qoorate"
	./stop-server $(CURDIR)

murder:
	echo "Murdering Qoorate"
	./murder-server
reload:
	echo "Reloading Qoorate"
	./reload-server $(CURDIR)

# truncate our logs
clear:
	echo "Truncating log files"
	>logs/error.log
	>logs/access.log
	>logs/qoorateserver.log
	>logs/uploader.log
	>profiles/run.log
	>profiles/error.log
	
