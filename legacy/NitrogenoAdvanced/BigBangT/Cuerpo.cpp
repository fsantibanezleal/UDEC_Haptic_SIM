//---------------------------------------------------------------------------
#pragma once
#pragma hdrstop

#include <windows.h>
#include <math.h>

#include "Cuerpo.h"

void NormalP(PoligonoReferido *vPoligono,float vPuntoA[3],float vPuntoB[3],float vPuntoC[3])
{
	register float vVectorA[3],vVectorB[3];
	vVectorA[0]=vPuntoB[0]-vPuntoA[0];
	vVectorA[1]=vPuntoB[1]-vPuntoA[1];
	vVectorA[2]=vPuntoB[2]-vPuntoA[2];
	
	vVectorB[0]=vPuntoC[0]-vPuntoA[0];
	vVectorB[1]=vPuntoC[1]-vPuntoA[1];
	vVectorB[2]=vPuntoC[2]-vPuntoA[2];

	vPoligono->normales[0]=(vVectorA[1]*vVectorB[2])-(vVectorA[2]*vVectorB[1]);
	vPoligono->normales[1]=(vVectorA[2]*vVectorB[0])-(vVectorA[0]*vVectorB[2]);
	vPoligono->normales[2]=(vVectorA[0]*vVectorB[1])-(vVectorA[1]*vVectorB[0]);

	GLfloat temp;
	temp =(GLfloat)sqrt( (GLdouble)pow(vPoligono->normales[0],2) + (GLdouble)pow(vPoligono->normales[1],2) + (GLdouble)pow(vPoligono->normales[2],2));
	temp =(GLfloat)( temp == 0.0 ? 1.0 : temp);
	vPoligono->normales[0] 	 =(GLfloat)( vPoligono->normales[0] / temp);
	vPoligono->normales[1] 	 =(GLfloat)( vPoligono->normales[1] / temp);
	vPoligono->normales[2] 	 =(GLfloat)( vPoligono->normales[2] / temp);
};

bool CuerpoCopiar(Cuerpo *vCuerpo,Cuerpo *vCuerpoOrigen,bool vCambio)
{
	register int i,j,k;
	if(!vCuerpoOrigen->existencia)
	{
		return false;
	}

	if(vCuerpo->existencia && vCambio)
	{
		vCuerpo->existencia=false;
		if(vCuerpo->numP>0)
		{
			delete[] vCuerpo->verPuntos;
		}
		if(vCuerpo->numN>0)
		{
			delete[] vCuerpo->verNormales;
		}
		if(vCuerpo->numT>0)
		{
			delete[] vCuerpo->verTexturas;
		}

		for(i=0;i<vCuerpo->numG;i++)
		{
			for(j=0;j<vCuerpo->partes[i].numCaras;j++)
			{
				if(vCuerpo->numP>0)
				{
					delete[] vCuerpo->partes[i].malla[j].indiceVertices;
				}
				if(vCuerpo->numN>0)
				{
					delete[] vCuerpo->partes[i].malla[j].indiceNormales;
				}
				if(vCuerpo->numT>0)
				{
					delete[] vCuerpo->partes[i].malla[j].indiceTexturas;
				}
			}
			delete[] vCuerpo->partes[i].malla;
		}
		delete[] vCuerpo->partes;
	}

	vCuerpo->existencia=true;
	vCuerpo->deseado=true;
	vCuerpo->colorRGBA=vCuerpoOrigen->colorRGBA;
	vCuerpo->normales=vCuerpoOrigen->normales;
	vCuerpo->texturas=vCuerpoOrigen->texturas;
	vCuerpo->numG=vCuerpoOrigen->numG;
	vCuerpo->numN=vCuerpoOrigen->numN;
	vCuerpo->numP=vCuerpoOrigen->numP;
	vCuerpo->numT=vCuerpoOrigen->numT;
	vCuerpo->pivote[0]=vCuerpoOrigen->pivote[0];
	vCuerpo->pivote[1]=vCuerpoOrigen->pivote[1];
	vCuerpo->pivote[2]=vCuerpoOrigen->pivote[2];

	vCuerpo->verPuntos=new float[3*vCuerpo->numP];
	for(i=0;i<3*vCuerpo->numP;i++)
	{
		vCuerpo->verPuntos[i]=vCuerpoOrigen->verPuntos[i];
	}

	if(vCuerpo->numN>0)
	{
		vCuerpo->verNormales=new float[3*vCuerpo->numN];
		for(i=0;i<3*vCuerpo->numN;i++)
		{
			vCuerpo->verNormales[i]=vCuerpoOrigen->verNormales[i];
		}
	}
	if(vCuerpo->numT>0)
	{
		vCuerpo->verTexturas=new float[3*vCuerpo->numT];
		for(i=0;i<3*vCuerpo->numT;i++)
		{
			vCuerpo->verTexturas[i]=vCuerpoOrigen->verTexturas[i];
		}
	}

	vCuerpo->partes=new MalladoReferido[vCuerpo->numG];
	for(i=0;i<vCuerpo->numG;i++)
	{
		vCuerpo->partes[i].deseado=vCuerpoOrigen->partes[i].deseado;
		vCuerpo->partes[i].numCaras=vCuerpoOrigen->partes[i].numCaras;
		vCuerpo->partes[i].malla=new PoligonoReferido[vCuerpo->partes[i].numCaras];
		for(j=0;j<vCuerpo->partes[i].numCaras;j++)
		{
			vCuerpo->partes[i].malla[j].colision=vCuerpoOrigen->partes[i].malla[j].colision;
			vCuerpo->partes[i].malla[j].numVertices=vCuerpoOrigen->partes[i].malla[j].numVertices;
			vCuerpo->partes[i].malla[j].indiceVertices=new int[vCuerpo->partes[i].malla[j].numVertices];
			if(vCuerpo->numN>0)
			{
				vCuerpo->partes[i].malla[j].indiceNormales=new int[vCuerpo->partes[i].malla[j].numVertices];
			}
			if(vCuerpo->numT>0)
			{
				vCuerpo->partes[i].malla[j].indiceTexturas=new int[vCuerpo->partes[i].malla[j].numVertices];
			}
			for(k=0;k<vCuerpo->partes[i].malla[j].numVertices;k++)
			{
				vCuerpo->partes[i].malla[j].indiceVertices[k]=vCuerpoOrigen->partes[i].malla[j].indiceVertices[k];
				if(vCuerpo->numN>0)
				{
					vCuerpo->partes[i].malla[j].indiceNormales[k]=vCuerpoOrigen->partes[i].malla[j].indiceNormales[k];
				}
				if(vCuerpo->numT>0)
				{
					vCuerpo->partes[i].malla[j].indiceTexturas[k]=vCuerpoOrigen->partes[i].malla[j].indiceTexturas[k];
				}
			}
		}
	}

	return true;
};

bool CuerpoDibujar(Cuerpo *vCuerpo,ColorGl *vColorM,bool vNormales,ColorGl *vColorN,bool vTexturas) // vModo: puntos, lineas, relleno
{
	register int	indice,indiceN,nC,nV,i,k;
	register float  vR,vG,vB,vNR,vNG,vNB,pABC[4][3];
	vR=(float)vColorM->Red();
	vG=(float)vColorM->Green();
	vB=(float)vColorM->Blue();
	vNR=(float)vColorN->Red();
	vNG=(float)vColorN->Green();
	vNB=(float)vColorN->Blue();

	if(vCuerpo->existencia && vCuerpo->deseado)
	{
		for(i=0;i<vCuerpo->numG;i++)
		{
			if(vCuerpo->partes[i].deseado)
			{
				nC=vCuerpo->partes[i].numCaras;
				for(int j=0;j< nC;j++) 
				{
					if(vCuerpo->partes[i].malla[j].colision)
					{
						glColor3d(1.0,0.0,0.0);
						vCuerpo->partes[i].malla[j].colision=false;
					}
					else
					{
						glColor3d(vR,vG,vB);
					}

					nV=vCuerpo->partes[i].malla[j].numVertices;
					glBegin(GL_POLYGON);

						for(k=0;k<nV;k++)
						{
							indice=3*(vCuerpo->partes[i].malla[j].indiceVertices[k]);
							pABC[k][0]=vCuerpo->verPuntos[indice+0];
							pABC[k][1]=vCuerpo->verPuntos[indice+1];
							pABC[k][2]=vCuerpo->verPuntos[indice+2];
						}

						NormalP(&vCuerpo->partes[i].malla[j],pABC[0],pABC[1],pABC[2]);
						glNormal3fv(vCuerpo->partes[i].malla[j].normales);

						for(k=0;k<nV;k++)
						{
							glVertex3fv(pABC[k]);
						}
					glEnd();
	
					if(vNormales && vCuerpo->normales)
					{
						glColor3d(vNR,vNG,vNB);
						for(k=0;k<nV;k++)
						{
							glBegin(GL_LINES);
								indice=3*(vCuerpo->partes[i].malla[j].indiceVertices[k]);
								indiceN=3*(vCuerpo->partes[i].malla[j].indiceNormales[k]);
								glVertex3d(vCuerpo->verPuntos[indice+0],vCuerpo->verPuntos[indice+1],vCuerpo->verPuntos[indice+2]);
								glVertex3d(vCuerpo->verNormales[indiceN+0]+vCuerpo->verPuntos[indice+0],vCuerpo->verNormales[indiceN+1]+vCuerpo->verPuntos[indice+1],vCuerpo->verNormales[indiceN+2]+vCuerpo->verPuntos[indice+2]);
							glEnd();			
						}
					}
				}
			}
		}
	}
	return true;
};

bool CuerpoActualizar(Cuerpo *vCuerpo,Cuerpo *vCuerpoOrigen,float vPosicion[3],float* vMatrizT) // vModo: puntos, lineas, relleno
{
	register int m;
	register float  vertice[3];

	if(vCuerpo->existencia && vCuerpo->deseado)
	{
		if(vCuerpo->numP!=vCuerpoOrigen->numP)
		{
			return false;
		}

		for(register int j=0;j< 3*vCuerpo->numP;j=j+3) 
		{
			vertice[0]=vCuerpoOrigen->verPuntos[j+0]-vPosicion[0];
			vertice[1]=vCuerpoOrigen->verPuntos[j+1]-vPosicion[1];
			vertice[2]=vCuerpoOrigen->verPuntos[j+2]-vPosicion[2];

			for(m=0;m<3;m++)
			{
				vCuerpo->verPuntos[j+m]=vertice[0]*vMatrizT[m]+vertice[1]*vMatrizT[m+4]+vertice[2]*vMatrizT[m+8]+1*vMatrizT[m+12];
				vCuerpo->verPuntos[j+m]+=vPosicion[m];
			}
		}
	}
	return true;
};


bool CuerpoEscalar(Cuerpo *vCuerpo,float vEscala[3],float vPivote[3])
{
	register int i,nP,nN,nMax;
	nP=3*vCuerpo->numP;
	nN=3*vCuerpo->numN;
	if(vCuerpo->numP>0 && vCuerpo->existencia)
	{
		nMax=(nP>nN)?nP:nN;
		for(i=0;i<nMax;i=i+3)
		{
			if(i<nP)
			{
				vCuerpo->verPuntos[i+0]=vCuerpo->verPuntos[i+0]*vEscala[0]+vPivote[0]*(1-vEscala[0]);
				vCuerpo->verPuntos[i+1]=vCuerpo->verPuntos[i+1]*vEscala[1]+vPivote[1]*(1-vEscala[1]);
				vCuerpo->verPuntos[i+2]=vCuerpo->verPuntos[i+2]*vEscala[2]+vPivote[2]*(1-vEscala[2]);
			}
			if(vCuerpo->normales && i<nN)
			{
				vCuerpo->verNormales[i+0]*=vEscala[0];
				vCuerpo->verNormales[i+1]*=vEscala[1];
				vCuerpo->verNormales[i+2]*=vEscala[2];
			}
		}
		return true;
	}
	return false;
};

bool CuerpoTrasladar(Cuerpo *vCuerpo,float vTrasX,float vTrasY,float vTrasZ)
{
	register int nP=3*vCuerpo->numP;

	vCuerpo->pivote[0]+=vTrasX;
	vCuerpo->pivote[1]+=vTrasY;
	vCuerpo->pivote[2]+=vTrasZ;

	if(vCuerpo->numP>0 && vCuerpo->existencia)
	{
		for(int i=0;i<nP;i=i+3)
		{
			vCuerpo->verPuntos[i+0]+=vTrasX;
			vCuerpo->verPuntos[i+1]+=vTrasY;
			vCuerpo->verPuntos[i+2]+=vTrasZ;
		}
		return true;
	}
	else
	{
		return false;
	}
};

bool CuerpoRotar(Cuerpo *vCuerpo,float vAngulo[3],float vPivote[3])
{
	register int i,nP;
	register GLdouble GRAD2RAD=3.14159265358979323846/180.0;

	register float mR[4*4];
	register float temp[3];
	
	nP=3*vCuerpo->numP;

	glPushMatrix();
		glMatrixMode(GL_MODELVIEW);
		glLoadIdentity();
		glRotatef(vAngulo[0],1,0,0);
		glRotatef(vAngulo[1],0,1,0);
		glRotatef(vAngulo[2],0,0,1);
		glGetFloatv(GL_MODELVIEW_MATRIX,  mR);
	glPopMatrix();
	
	if(vCuerpo->numP>0 && vCuerpo->existencia)
	{
		for(i=0;i<nP;i=i+3)
		{
			vCuerpo->verPuntos[i+0]-=vPivote[0];
			vCuerpo->verPuntos[i+1]-=vPivote[1];
			vCuerpo->verPuntos[i+2]-=vPivote[2];

			temp[0]=vCuerpo->verPuntos[i+0]*mR[0]+vCuerpo->verPuntos[i+1]*mR[4]+vCuerpo->verPuntos[i+2]*mR[8]+1*mR[12];
			temp[1]=vCuerpo->verPuntos[i+0]*mR[1]+vCuerpo->verPuntos[i+1]*mR[5]+vCuerpo->verPuntos[i+2]*mR[9]+1*mR[13];
			temp[2]=vCuerpo->verPuntos[i+0]*mR[2]+vCuerpo->verPuntos[i+1]*mR[6]+vCuerpo->verPuntos[i+2]*mR[10]+1*mR[14];

			vCuerpo->verPuntos[i+0]=temp[0]+vPivote[0];
			vCuerpo->verPuntos[i+1]=temp[1]+vPivote[1];
			vCuerpo->verPuntos[i+2]=temp[2]+vPivote[2];
		}
		return true;
	}
	else
	{
		return false;
	}
};
