#include <lib/components/tuxtxtapp.h>
#include <lib/base/init.h>
#include <lib/base/init_num.h>
#include <lib/driver/rc.h>
#include <lib/gdi/lcd.h>
#include <lib/gdi/fb.h>

extern "C" int tuxtxt_run_ui(int pid, int demux);
extern "C" int tuxtxt_init();
extern "C" void tuxtxt_start(int tpid, int demux);
extern "C" int tuxtxt_stop();
extern "C" void tuxtxt_close();

eAutoInitP0<eTuxtxtApp> init_eTuxtxtApp(eAutoInitNumbers::lowlevel, "Tuxtxt");
eTuxtxtApp *eTuxtxtApp::instance;

eTuxtxtApp::eTuxtxtApp() : pid(0), enableTtCaching(false), uiRunning(false)
{
	pthread_mutex_init( &cacheChangeLock, 0 );
	if (!instance)
		instance=this;
}

eTuxtxtApp::~eTuxtxtApp()
{
	if (instance==this)
		instance=0;
	kill();
	pthread_mutex_destroy( &cacheChangeLock );
}

int eTuxtxtApp::startUi()
{
	if (pid && fbClass::getInstance()->lock() >= 0)
	{
		eDBoxLCD::getInstance()->lock();
		eRCInput::getInstance()->lock();
		pthread_mutex_lock( &cacheChangeLock );
		uiRunning = true;
		pthread_mutex_unlock( &cacheChangeLock );
		run();
	}
	return 0;
}

void eTuxtxtApp::thread()
{
	hasStarted();
	tuxtxt_run_ui(pid, demux);
}

void eTuxtxtApp::thread_finished()
{
	uiRunning = false;
	eRCInput::getInstance()->unlock();
	eDBoxLCD::getInstance()->unlock();
	eDBoxLCD::getInstance()->update();
	fbClass::getInstance()->unlock();
}

void eTuxtxtApp::initCache()
{
	if (enableTtCaching)
		tuxtxt_init();
}

void eTuxtxtApp::freeCache()
{
	pthread_mutex_lock( &cacheChangeLock );
	if ( !uiRunning )
	{
		tuxtxt_close();
		pid = 0;
	}
	pthread_mutex_unlock( &cacheChangeLock );
}

void eTuxtxtApp::startCaching( int tpid, int tdemux)
{
	pid = tpid;
	demux = tdemux;
	if (enableTtCaching)
		tuxtxt_start(pid, demux);
}

void eTuxtxtApp::stopCaching()
{
	pthread_mutex_lock( &cacheChangeLock );
	if ( !uiRunning )
		tuxtxt_stop();

	pthread_mutex_unlock( &cacheChangeLock );
}

void eTuxtxtApp::setEnableTtCachingOnOff( int onoff )
{
	if (onoff && !enableTtCaching)		// Switch caching on
	{
		enableTtCaching = true;
		if (pid)
		{
			initCache();
			startCaching(pid, demux);
		}
	}
	else if (!onoff && enableTtCaching)	// Switch caching off
	{
		enableTtCaching = false;
		int savePid = pid;
		freeCache();
		pid = savePid;
	}
}