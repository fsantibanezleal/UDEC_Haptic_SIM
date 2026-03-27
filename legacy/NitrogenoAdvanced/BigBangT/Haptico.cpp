#include <windows.h>

#include "Haptico.h" 


static	HHD              ghHD;
static	hduVector3Dd	 gAnchorPosition;
static	HDboolean		 gIsAnchorActive;


HDCallbackCode HDCALLBACK touchScene(void *pUserData);
HDCallbackCode HDCALLBACK copyHapticDisplayState(void *pUserData);

/////////////////////////////////////////////////////////////////////////////////////////////////

Haptico::~Haptico()
{
	delete transformacion;
    //atexit(exitHandler);
	exitHandler();
};

Haptico::Haptico()
{
	transformacion= new float[16];		

	creacion=true;
	habilitado=false;

	ghHD = HD_INVALID_HANDLE;
	hUpdateDeviceCallback = HD_INVALID_HANDLE;

	kCursorScreenSize = 20.0;
	gCursorDisplayList = 0;
	gCursorScale = 1.0;

	gIsAnchorActive = FALSE;
	activo=false;

	HDErrorInfo error;
	ghHD = hdInitDevice("Default PHANToM");
	if (HD_DEVICE_ERROR(error = hdGetError())) 
	{
		creacion=false;
		//hduPrintError(stderr, &error, "Failed to initialize haptic device");
		//fprintf(stderr, "\nPress any key to quit.\n");
		//getchar();
		//exit(-1);
	}

	if(creacion)
	{
		hdEnable(HD_FORCE_OUTPUT);
	        
		hUpdateDeviceCallback = hdScheduleAsynchronous(touchScene, 0, HD_MAX_SCHEDULER_PRIORITY);

		hdStartScheduler();
		if (HD_DEVICE_ERROR(error = hdGetError()))
		{
			hduPrintError(stderr, &error, "Failed to start the scheduler");
			exit(-1);
			creacion=false;
		}
	}
};


int Haptico::exitHandler(void)
{
    hdStopScheduler();
    hdUnschedule(hUpdateDeviceCallback);

    if (ghHD != HD_INVALID_HANDLE)
    {
        hdDisableDevice(ghHD);
        ghHD = HD_INVALID_HANDLE;
    }

    return 0;    
};

void Haptico::Actualizar()
{
    HapticDisplayState estado;
    hdScheduleSynchronous(copyHapticDisplayState, &estado,HD_DEFAULT_SCHEDULER_PRIORITY);
	activo=(bool) estado.isAnchorActive;
    //drawCursor(&state);
    //if (state.isAnchorActive)
    //{
    //    drawAnchor(&state);
    //}
	
	transformacion=estado.transform;
	posicion[0]=estado.position[0];
	posicion[1]=estado.position[1];
	posicion[2]=estado.position[2];
};


void Haptico::drawCursor(const HapticDisplayState *pState)
{
    static const double kCursorRadius = 0.5;
    static const double kCursorHeight = 1.5;
    static const int kCursorTess = 15;

    GLUquadricObj *qobj = 0;

    glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT | GL_LIGHTING_BIT);
		glPushMatrix();
			if (!gCursorDisplayList)
			{
				gCursorDisplayList = glGenLists(1);
				glNewList(gCursorDisplayList, GL_COMPILE);
				qobj = gluNewQuadric();
		               
				gluCylinder(qobj, 0.0, kCursorRadius, kCursorHeight,kCursorTess, kCursorTess);
					glTranslated(0.0, 0.0, kCursorHeight);
					gluCylinder(qobj, kCursorRadius, 0.0, kCursorHeight / 5.0,kCursorTess, kCursorTess);
		    
				gluDeleteQuadric(qobj);
				glEndList();
			}
		    
			glMultMatrixd(workspacemodel);
			glMultMatrixf(pState->transform);
			glScaled(gCursorScale, gCursorScale, gCursorScale);

			glEnable(GL_COLOR_MATERIAL);
			glColor3f(0.0, 0.5, 1.0);

			glCallList(gCursorDisplayList);
		glPopMatrix(); 
    glPopAttrib();
};

void Haptico::drawAnchor(const HapticDisplayState *pState)
{
    glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT);
        glPushMatrix();
            glMultMatrixd(workspacemodel);
            glLineWidth(2.0);
            glEnable(GL_COLOR_MATERIAL);
            glColor3f(1.0, 0.0, 0.0);
            glBegin(GL_LINES);
                glVertex3fv(pState->position);
                glVertex3fv(pState->anchor);
            glEnd();
			glLineWidth(1.0);
        glPopMatrix();
    glPopAttrib();
};


void Haptico::updateWorkspace()
{
    HDdouble screenTworkspace;
    GLdouble modelview[16];
    GLdouble projection[16];
    GLint viewport[4];

    glGetDoublev(GL_MODELVIEW_MATRIX, modelview);
    glGetDoublev(GL_PROJECTION_MATRIX, projection);
    glGetIntegerv(GL_VIEWPORT, viewport);

    hduMapWorkspaceModel(modelview, projection, workspacemodel);
    screenTworkspace = hduScreenToWorkspaceScale(modelview, projection, viewport, workspacemodel);
    gCursorScale = kCursorScreenSize * screenTworkspace;
};

HDCallbackCode HDCALLBACK touchScene(void *pUserData)
{
	static const HDdouble kAnchorStiffness = 0.2;

	int currentButtons, lastButtons;
	hduVector3Dd position;
	hduVector3Dd force;
	force.set(0,0,0);
	HDdouble forceClamp;
	HDErrorInfo error;

	hdBeginFrame(ghHD);
    
    	hdGetIntegerv(HD_CURRENT_BUTTONS, &currentButtons);
    	hdGetIntegerv(HD_LAST_BUTTONS, &lastButtons);
    
    	if ((currentButtons & HD_DEVICE_BUTTON_1) != 0 &&
    		(lastButtons & HD_DEVICE_BUTTON_1) == 0)
    	{
    		gIsAnchorActive = TRUE;
    		hdGetDoublev(HD_CURRENT_POSITION, gAnchorPosition);
    	}
    	else if ((currentButtons & HD_DEVICE_BUTTON_1) == 0 &&
    			 (lastButtons & HD_DEVICE_BUTTON_1) != 0)
    	{
    		gIsAnchorActive = FALSE;
    	}   
    
    	if (gIsAnchorActive)
    	{
    		hdGetDoublev(HD_CURRENT_POSITION, position);
    
    		//F = k * (anchor - position)
    		hduVecSubtract(force, gAnchorPosition, position);
    		hduVecScaleInPlace(force, kAnchorStiffness);
    		hdGetDoublev(HD_NOMINAL_MAX_CONTINUOUS_FORCE, &forceClamp);
    		if (hduVecMagnitude(force) > forceClamp)
    		{
    			hduVecNormalizeInPlace(force);
    			hduVecScaleInPlace(force, forceClamp);
    		}
    	}
    
    	hdSetDoublev(HD_CURRENT_FORCE, force);
   
	hdEndFrame(ghHD);

	if (HD_DEVICE_ERROR(error = hdGetError()))
	{
		if (hduIsForceError(&error))
		{
			gIsAnchorActive = FALSE;
		}
		else
		{
			hduPrintError(stderr, &error, "Error during haptic rendering");
			exit(-1);
		}
	}

	return HD_CALLBACK_CONTINUE;
};

HDCallbackCode HDCALLBACK copyHapticDisplayState(void *pUserData)
{
	HapticDisplayState *pState = (HapticDisplayState *) pUserData;

	pState->isAnchorActive = gIsAnchorActive;

	memcpy(pState->anchor, gAnchorPosition, sizeof(hduVector3Df));

	hdGetFloatv(HD_CURRENT_TRANSFORM, pState->transform);
	hdGetFloatv(HD_CURRENT_POSITION, pState->position);

	return HD_CALLBACK_DONE;
};
