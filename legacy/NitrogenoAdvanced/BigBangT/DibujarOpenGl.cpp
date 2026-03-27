//---------------------------------------------------------------------------
#pragma once
#pragma hdrstop

#include <windows.h>

#include "DibujarOpenGl.h"

using namespace System::Windows::Forms;
//---------------------------------------------------------------------------
void DibujarOpenGl::Inicializar()
{

	ProyPers=false;
	dibNormal=false;
	rehacerDibujo=true;
	swTestP=true;
	swModel=true;
	swFace=true;
	swOcul=false;
	swPStip=false;

	indiceObjetoActivo=indiceObjetoHaptico=indiceObjetoHapticoAnt=1;
	rendSelec=1;
	ilumSelec=1;

	swPStipMask=0;
	swBackType=1;
	swFrontType=1;


	visualR= new float[3];
	visualS= new float[3];
	visualT= new float[3];
	
	visualT[0]=visualT[1]=visualT[2]=visualR[0]=visualR[1]=visualR[2]=0.0;
	visualS[0]=visualS[1]=visualS[2]=1.0;

	limites= new float[6];
	limites[0]=limites[2]=limites[4]=(float)-180.0;
	limites[1]=limites[3]=limites[5]=(float)180.0;

	DXYZ= new float[3];
	DXYZ[0]=limites[1]-limites[0];
	DXYZ[1]=limites[3]-limites[2];
	DXYZ[2]=limites[5]-limites[4];

	triangulos=new Poligono[2];
	triangulos[0].numVertices=3;
	triangulos[0].colision=false;
	triangulos[0].colorRGBA.SetColorGl(0.0,1.0,0.0);
	triangulos[0].n=true;
	triangulos[0].t=false;
	triangulos[0].vertices=new float[3*triangulos[0].numVertices];
	triangulos[0].vertices[0]=-1.0;
	triangulos[0].vertices[1]=0.0;
	triangulos[0].vertices[2]=1.0;
	if(triangulos[0].n)
	{
		triangulos[0].normales=new float[triangulos[0].numVertices];
	}
	if(triangulos[0].t)
	{
		triangulos[0].texturas=new float[triangulos[0].numVertices];
	}
	triangulos[1].numVertices=3;
	triangulos[1].colision=false;
	triangulos[1].colorRGBA.SetColorGl(0.0,0.0,1.0);
	triangulos[1].n=true;
	triangulos[1].t=false;
	triangulos[1].vertices=new float[triangulos[1].numVertices];
	triangulos[1].vertices[0]=-1.0;
	triangulos[1].vertices[1]=0.0;
	triangulos[1].vertices[2]=1.0;
	if(triangulos[1].n)
	{
		triangulos[1].normales=new float[triangulos[1].numVertices];
	}
	if(triangulos[1].t)
	{
		triangulos[1].texturas=new float[triangulos[1].numVertices];
	}
	
	colorObjetos= new ColorGl();
	colorObjetos->SetColorGl(0.9,0.9,0.9,1.0);
	colorNormales= new ColorGl();
	colorNormales->SetColorGl(0.2,0.2,0.2,1.0);

	octreePrincipal=NULL;

	dibOctree=false;

	octreeRuta= new RutaPuntos;
	octreeRuta->factorC=false;				// false indica que debe seguir dividiendo aunque el subbloque haya herado todos los puntos de su padre.... true indica que no...
	octreeRuta->factorG=(float)(1.0/50.0);	// Regulable... para mi es (2^3subespaciosDirectos)^2Profundidad..0.125 % IMplica que se requiera que un bloque octre contenga al menos un 12.5% de su los puntos de su padre para dividirse
	octreeRuta->factorR=(float)0.01;		// Regulable.... porcentaje del espacio minimo a usar por un octree.. es decir no habran bloques de dimensiones menor a este porcentaje del octree principal
	octreeRuta->factorU=4;					// Regulable... algo asi como el numero de puntos minimos para la division
	
	octreeRuta->numCuerpos=0;
	octreeRuta->numPuntosT=0;
	octreeRuta->octreeAnteriorActual=NULL;


	superHaptico= new Haptico();
	if(!superHaptico->creacion)
	{
		MessageBox::Show("No se ha podido inicializar el Dispositivo haptico");
	}
	matrizT=new double[16];
}

//-------------------------Definidas-------------------------------------
void DibujarOpenGl::Resize(int w, int h)
{
	h==0?h=1:h=h;
	w==0?w=1:w=w;
	glViewport(0,0,(GLint)w,(GLint)h);

	if(ProyPers)
	{
		static const double kPI = 3.1415926535897932384626433832795;
		static const double kFovY = 40;

		double nearDist, farDist, aspect;

		nearDist = 1.0 / tan((kFovY / 2.0) * kPI / 180.0);
		farDist = nearDist + 1000.0;
		aspect = (double) w/ h;
	   
		glMatrixMode(GL_PROJECTION);
		glLoadIdentity();
		gluPerspective(kFovY, aspect, nearDist, farDist);

		glMatrixMode(GL_MODELVIEW);
		glLoadIdentity();            
		gluLookAt(0, 0, nearDist + 1,0, 0, 0,0, 1, 0);
	}
	else
	{
		glMatrixMode(GL_PROJECTION);
		glLoadIdentity();
		glOrtho(-100,100,-100,100,-1000,1000);

		glMatrixMode(GL_MODELVIEW);
		glLoadIdentity();            
		gluLookAt(0,0,900,0,0,0,0,1,0);
		
		glClearColor((GLclampf)0.7,(GLclampf)0.7,(GLclampf)0.7,1.0);
	}
    
    if(superHaptico->creacion && superHaptico->habilitado)
	{
		superHaptico->updateWorkspace();
	}
}


void DibujarOpenGl::Renderizar(HDC hdcActual)
{
	//CFondo.Red(),CFondo.Green(),CFondo.Blue(),CFondo.Alpha()
	glClearColor((GLclampf)0.7,(GLclampf)0.7,(GLclampf)0.7,1.0);
	Selecciones();
//	glDrawBuffer(GL_FRONT);
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glPushMatrix();
		glScalef(visualS[0],visualS[1],visualS[1]);
		glTranslatef(visualT[0],visualT[1],visualT[2]);
		glRotatef(visualR[0],1,0,0);
		glRotatef(visualR[1],0,1,0);
		glRotatef(visualR[2],0,0,1);
		Coordenadas();
		LightP(ilumSelec);
		SelecRender(rendSelec);
	glPopMatrix();

	glFlush();
	SwapBuffers(hdcActual);
}

void DibujarOpenGl::SelecRender(GLint RrndSelec)
{
	switch (rendSelec)
	{
		case 0:
			Dibujo4();
			break;
		case 1:
			Dibujo1();
			break;
		case 2:
			Dibujo2();
			break;
		case 3:
			Dibujo3();
			break;
		case 4:
			Dibujo4();
			break;
		case 5:
			Dibujo5();
			break;
		case 6:
			Dibujo6();
			break;

		default:
			Dibujo4();
			break;
	}
}

void DibujarOpenGl::Selecciones()
{
	if(swTestP)
	{
		glEnable(GL_DEPTH_TEST);
//		glDepthFunc(GL_LEQUAL);
	}
	else
	{
		glDisable(GL_DEPTH_TEST);
	}
	swModel	? glShadeModel(GL_FLAT):glShadeModel(GL_SMOOTH);
	swFace	? glFrontFace(GL_CW):glFrontFace(GL_CCW);
	swOcul	? glEnable(GL_CULL_FACE):glDisable(GL_CULL_FACE);
	swPStip	? glEnable(GL_POLYGON_STIPPLE):glDisable(GL_POLYGON_STIPPLE);

	switch (swBackType)
	{
		case 0:
			glPolygonMode(GL_BACK,GL_FILL);
			break;
		case 1:
			glPolygonMode(GL_BACK,GL_LINE);
		break;
		case 2:
			glPolygonMode(GL_BACK,GL_POINT);
		break;
		default:
			glPolygonMode(GL_BACK,GL_FILL);
	}
	switch (swFrontType)
	{
		case 0:
			glPolygonMode(GL_FRONT,GL_FILL);
			break;
		case 1:
			glPolygonMode(GL_FRONT,GL_LINE);
		break;
		case 2:
			glPolygonMode(GL_FRONT,GL_POINT);
		break;
		default:
			glPolygonMode(GL_FRONT,GL_FILL);
	}
}

void DibujarOpenGl::LightP(GLint ilumSelec)
{
	switch (ilumSelec)
	{
		default:
		{
			GLfloat ambientLight[] = { 0.3f, 0.3f, 0.3f, 1.0f };
			GLfloat diffuseLight[] = { 1.0f, 1.0f, 1.0f, 1.0f };
			GLfloat lightPos[] = { 5.0f, 5.0f, -1.0f, 1.0f };
			glEnable(GL_LIGHTING);
			glClearDepth(1.0f);

			glLightfv(GL_LIGHT0,GL_AMBIENT,ambientLight);
			glLightfv(GL_LIGHT0,GL_DIFFUSE,diffuseLight);
			glLightfv(GL_LIGHT0,GL_POSITION,lightPos);
			glEnable(GL_LIGHT0);

			glEnable(GL_COLOR_MATERIAL);

			glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE);
			break;
		}
		case 0:
		{
			GLfloat ambientLight[] = { 0.9f, 0.3f, 0.3f, 1.0f };
			GLfloat diffuseLight[] = { 0.7f, 0.7f, 0.7f, 1.0f };
			glLightfv(GL_LIGHT0,GL_AMBIENT,ambientLight);
			glLightfv(GL_LIGHT0,GL_DIFFUSE,diffuseLight);
			GLfloat lightPos[] = { -50.f, 50.0f, -100.0f, 1.0f };
			glLightfv(GL_LIGHT0,GL_POSITION,lightPos);

			glEnable(GL_LIGHTING);
			glLightModelfv(GL_LIGHT_MODEL_AMBIENT, ambientLight);
			glEnable(GL_COLOR_MATERIAL);
			glColorMaterial(GL_FRONT,GL_AMBIENT_AND_DIFFUSE);
			break;
		}
		case 1:
		{
			GLfloat ambientLight[] = { 0.3f, 0.3f, 0.3f, 1.0f };
			GLfloat diffuseLight[] = { 0.3f, 0.3f, 0.3f, 1.0f };
			GLfloat specular[]= {0.3f, 0.3f, 0.3f, 1.0f};
			GLfloat specref[]={0.2f,0.2f,0.2f,1.0f};
			GLfloat lightPos[] = { 0.0f, 0.0f, 1000.0f, 1.0f };
			glEnable(GL_LIGHTING);
			glLightfv(GL_LIGHT0,GL_AMBIENT,ambientLight);
			glLightfv(GL_LIGHT0,GL_DIFFUSE,diffuseLight);
			glLightfv(GL_LIGHT0,GL_SPECULAR,specular);
			glLightfv(GL_LIGHT0,GL_POSITION,lightPos);
			glEnable(GL_LIGHT0);
			glEnable(GL_COLOR_MATERIAL);
			glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE);
			glMaterialfv(GL_FRONT, GL_SPECULAR, specref);
			glMateriali(GL_FRONT, GL_SHININESS,16);
			//glMaterialfv(GL_BACK, GL_SPECULAR, specref);
			//glMateriali(GL_BACK, GL_SHININESS,64);

			break;
		}
	}
}

void DibujarOpenGl::Coordenadas()
{

	glLineWidth(1.0);
	glBegin(GL_LINES);
	//CEjes.Red(),0.0,0.0,CEjes.Alpha()
		glColor4d(1.0,0.0,0.0,1.0);
		glVertex3d(1000.0,0.0, 0.0);
		glVertex3d(-1000.0,0.0, 0.0);

		glColor4d(0.0,1.0,0.0,1.0);
		glVertex3d(0.0,1000.0, 0.0);
		glVertex3d(0.0,-1000.0, 0.0);

		glColor4d(0.0,0.0,1.0,1.0);
		glVertex3d(0.0,0.0, 1000.0);
		glVertex3d(0.0,0.0, -1000.0);
	glEnd();
	glBegin(GL_TRIANGLES);
		glColor4d(1.0,0.0,0.0,1.0);
		glVertex3d(1000.0,0.0,0.0);
		glVertex3d(990,10,0.0);
		glVertex3d(990,-10,0.0);
		glVertex3d(-1000.0,0.0,0.0);
		glVertex3d(-990,10,0.0);
		glVertex3d(-990,-10,0.0);

		glColor4d(0.0,1.0,0.0,1.0);
		glVertex3d(0.0,1000.0,0.0);
		glVertex3d(-10,990,0.0);
		glVertex3d(10,990,0.0);
		glVertex3d(0.0,-1000,0.0);
		glVertex3d(-10,-990,0.0);
		glVertex3d(10,-990,0.0);

		glColor4d(0.0,0.0,1.0,1.0);
		glVertex3d(0.0,0.0,1000);
		glVertex3d(0.0,10,990);
		glVertex3d(0.0,-10,990);
		glVertex3d(0.0,0.0,-1000);
		glVertex3d(0.0,10,-1000);
		glVertex3d(0.0,-10,-1000);
	glEnd();
}

void DibujarOpenGl::Dibujo1()
{
	register int i;
	register int nE=numObjetosEstablecidos;

	for(i=1;i<=nE;i++)
	{
		if(superHaptico->creacion && superHaptico->habilitado)
		{
			if(indiceObjetoHaptico==i)
			{
				if(!CuerpoDibujar(&Objetos[0],&Objetos[i].colorRGBA,dibNormal,colorNormales,false))
				{
					MessageBox::Show("Error al dibujar");
				}
			}
			else 
			{
				if(!CuerpoDibujar(&Objetos[i],colorObjetos,dibNormal,colorNormales,false))
				{
					MessageBox::Show("Error al dibujar");
				}
			}
		}
		else if(!CuerpoDibujar(&Objetos[i],&Objetos[i].colorRGBA,dibNormal,colorNormales,false))
		{
			MessageBox::Show("Error al dibujar");
		}
	}
	if(dibOctree && octreePrincipal!=NULL)
	{
		glPolygonMode(GL_BACK,GL_LINE);
		glPolygonMode(GL_FRONT,GL_LINE);
		DibujarOctree(octreePrincipal);
	}
}

void DibujarOpenGl::Dibujo2()
{
	glBegin(GL_POLYGON);
		for(register int k=0;k<3;k++)
		{
			//glVertex3d(vCuerpo->verPuntos[indice+0],vCuerpo->verPuntos[indice+1],vCuerpo->verPuntos[indice+2]);
		}
	glEnd();
}

void DibujarOpenGl::Dibujo3()
{
;
}

void DibujarOpenGl::Dibujo4()
{
;
}
void DibujarOpenGl::Dibujo5()
{
}

void DibujarOpenGl::Dibujo6()
{
	glPushMatrix();
		glColor3d(0.2,0.5,0.6);
		glBegin(GL_POLYGON);
			glVertex3d(0.0,0.0,0.0);
			glVertex3d(3.0,0.0,0.0);
			glVertex3d(3.0,0.0,3.0);
			glVertex3d(0.0,0.0,3.0);
		glEnd();
	glPopMatrix();
}


///////////////////////////////////////////////////////// Funciones de acople

int DibujarOpenGl::SelecObjeto(GLuint vObjeto)
{
	if(vObjeto>=1 && vObjeto <= numObjetosEstablecidos )
	{
		indiceObjetoActivo=vObjeto;
	}
	else if(vObjeto<1)
	{	
		indiceObjetoActivo=numObjetosEstablecidos-1;
	}
	else if (vObjeto>numObjetosEstablecidos)
	{
		indiceObjetoActivo=1;
	}
	return indiceObjetoActivo;
}