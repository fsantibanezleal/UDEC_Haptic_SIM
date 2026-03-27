#include <windows.h>

#include "HapticoDoble.h" 


static	HHD              ghHD[2];
static	hduVector3Dd	 gAnchorPosition[2];
static	HDboolean		 gIsAnchorActive[2];


HDCallbackCode HDCALLBACK touchSceneDoble(void *pUserData);
HDCallbackCode HDCALLBACK copyHapticDisplayStateDoble(void *pUserData);

/////////////////////////////////////////////////////////////////////////////////////////////////

HapticoDoble::~HapticoDoble()
{
    //atexit(exitHandler);
	exitHandler();
};

HapticoDoble::HapticoDoble()
{
	creacion[0]=creacion[1]=true;

	habilitado[0]=habilitado[1]=false;



	ghHD[0]=ghHD[1]= HD_INVALID_HANDLE;
	hUpdateDeviceCallback = HD_INVALID_HANDLE;

	kCursorScreenSize[0]=kCursorScreenSize[1]= 20.0;
	gCursorDisplayList[0]=gCursorDisplayList[1]= 0;
	gCursorScale[0]=gCursorScale[1]= 1.0;

	gIsAnchorActive[0]=gIsAnchorActive[1]= FALSE;

	HDErrorInfo error;

	ghHD[0] = hdInitDevice("Default PHANToM");
	if (HD_DEVICE_ERROR(error = hdGetError())) 
	{
		creacion[0]=false;
	}

	ghHD[1] = hdInitDevice("PHANToM 2");
	if (HD_DEVICE_ERROR(error = hdGetError())) 
	{
		creacion[0]=false;
	}

	if(creacion[0] && creacion[1])
	{
		hdEnable(HD_FORCE_OUTPUT);
	        
		hUpdateDeviceCallback = hdScheduleAsynchronous(touchSceneDoble, 0, HD_MAX_SCHEDULER_PRIORITY);

		hdStartScheduler();
		if (HD_DEVICE_ERROR(error = hdGetError()))
		{
			creacion[0]=creacion[1]=false;
		}
	}
};


int HapticoDoble::exitHandler(void)
{
    hdStopScheduler();
    hdUnschedule(hUpdateDeviceCallback);

    if (ghHD[0] != HD_INVALID_HANDLE)
    {
        hdDisableDevice(ghHD[0]);
        ghHD[0] = HD_INVALID_HANDLE;
    }
    if (ghHD[1] != HD_INVALID_HANDLE)
    {
        hdDisableDevice(ghHD[1]);
        ghHD[1] = HD_INVALID_HANDLE;
    }

    return 0;    
};

void HapticoDoble::Actualizar()
{
    HapticDisplayState estado;

	for(register int j=0;j<2;j++)
	{
		hdMakeCurrentDevice(ghHD[j]);
		hdScheduleSynchronous(copyHapticDisplayStateDoble, &estado,HD_DEFAULT_SCHEDULER_PRIORITY);
		//memcpy(pivote[j], gAnchorPosition[j], sizeof(hduVector3Df));
		activo[j]=(bool) gIsAnchorActive[j];
		for(register int i=0;i<16;i++)
		{
			transformacion[j][i]=estado.transform[i];
		}
		posicion[j][0]=estado.position[0];
		posicion[j][1]=estado.position[1];
		posicion[j][2]=estado.position[2];
	}
};

void HapticoDoble::drawAnchor(const HapticDisplayState *pState)
{
    glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT);
        glPushMatrix();
            glMultMatrixd(&workspacemodel[0][0]);
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


void HapticoDoble::updateWorkspace()
{
    HDdouble screenTworkspace;
    GLdouble modelview[16];
    GLdouble projection[16];
    GLint viewport[4];

    glGetDoublev(GL_MODELVIEW_MATRIX, modelview);
    glGetDoublev(GL_PROJECTION_MATRIX, projection);
    glGetIntegerv(GL_VIEWPORT, viewport);

    hduMapWorkspaceModel(modelview, projection, &workspacemodel[0][0]);
    screenTworkspace = hduScreenToWorkspaceScale(modelview, projection, viewport, &workspacemodel[0][0]);
    gCursorScale[0] = kCursorScreenSize[0] * screenTworkspace;
	gCursorScale[1] = kCursorScreenSize[1] * screenTworkspace;
};

HDCallbackCode HDCALLBACK touchSceneDoble(void *pUserData)
{
	static const HDdouble kAnchorStiffness[2] = {0.2 , 0.2};

	register int j;
	int currentButtons, lastButtons;
	hduVector3Dd position[2];
	hduVector3Dd force[2],tempF;
	force[0].set(0,0,0);
	force[1].set(0,0,0);
	HDdouble forceClamp[2];
	HDErrorInfo error;

	for(j=0;j<2;j++)
	{
		hdMakeCurrentDevice(ghHD[j]);

		hdBeginFrame(ghHD[j]);
	    
    		hdGetIntegerv(HD_CURRENT_BUTTONS, &currentButtons);
    		hdGetIntegerv(HD_LAST_BUTTONS, &lastButtons);
	    
    		if ((currentButtons & HD_DEVICE_BUTTON_1) != 0 &&
    			(lastButtons & HD_DEVICE_BUTTON_1) == 0)
    		{
    			gIsAnchorActive[j] = TRUE;
    			hdGetDoublev(HD_CURRENT_POSITION, gAnchorPosition[0]);
				hdGetDoublev(HD_CURRENT_POSITION, gAnchorPosition[1]);
    		}
    		else if ((currentButtons & HD_DEVICE_BUTTON_1) == 0 &&
    				 (lastButtons & HD_DEVICE_BUTTON_1) != 0)
    		{
    			gIsAnchorActive[j] = FALSE;
    		}   
			hdGetDoublev(HD_CURRENT_POSITION, position[j]);	    
		hdEndFrame(ghHD[j]);

		if (HD_DEVICE_ERROR(error = hdGetError()))
		{
			if (hduIsForceError(&error))
			{
				gIsAnchorActive[j] = FALSE;
			}
			else
			{
				hduPrintError(stderr, &error, "Error during haptic rendering");
				exit(-1);
			}
		}
	}

	for(j=0;j<2;j++)
	{
		hdMakeCurrentDevice(ghHD[j]);

		hdBeginFrame(ghHD[j]);

			if (gIsAnchorActive[j])
			{
				//F[x1] =- k * (anchor[x0] - position[x0])
				hduVecSubtract(tempF, position[(j==1)?1:0], gAnchorPosition[(j==1)?1:0]);
				hduVecScaleInPlace(tempF, kAnchorStiffness[(j==0)?1:0]);
				hduVecSubtract(force[(j==0)?1:0], gAnchorPosition[(j==0)?1:0], position[(j==0)?1:0]);
    			hduVecScaleInPlace(force[(j==0)?1:0], kAnchorStiffness[(j==0)?1:0]);

				hduVecAdd(force[(j==0)?1:0],tempF,force[(j==0)?1:0]);

    			hdGetDoublev(HD_NOMINAL_MAX_CONTINUOUS_FORCE, &forceClamp[(j==0)?1:0]);
    			if (hduVecMagnitude(force[(j==0)?1:0]) > forceClamp[(j==0)?1:0])
    			{
    				hduVecNormalizeInPlace(force[(j==0)?1:0]);
    				hduVecScaleInPlace(force[(j==0)?1:0], forceClamp[(j==0)?1:0]);
    			}
			}

			hdSetDoublev(HD_CURRENT_FORCE, force[j]);
	   
		hdEndFrame(ghHD[j]);

		if (HD_DEVICE_ERROR(error = hdGetError()))
		{
			if (hduIsForceError(&error))
			{
				gIsAnchorActive[j] = FALSE;
			}
			else
			{
				hduPrintError(stderr, &error, "Error during haptic rendering");
				exit(-1);
			}
		}
	}

	return HD_CALLBACK_CONTINUE;
};

HDCallbackCode HDCALLBACK copyHapticDisplayStateDoble(void *pUserData)
{
	HapticDisplayState *pState = (HapticDisplayState *) pUserData;

	hdGetFloatv(HD_CURRENT_TRANSFORM, pState->transform);
	hdGetFloatv(HD_CURRENT_POSITION, pState->position);

	return HD_CALLBACK_DONE;
};
