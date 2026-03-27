//---------------------------------------------------------------------------
#pragma once
#pragma hdrstop

#include <windows.h>
#include <math.h>

#include "InteraccionTT.h"
#include "Octrees.h"

using namespace System::Windows::Forms;
//---------------------------------------------------------------------------
//---------------------------------------------------------------------------

bool CrearRuta(RutaPuntos *vRuta,Cuerpo *vCuerpo,int vElementos)
{
	if(vElementos!=vRuta->numCuerpos)
	{
		delete[] vRuta->octreeAnteriorActual;

		vRuta->numPuntosT=0;
		vRuta->numCuerpos=vElementos;

		for(register int i=1;i<=vElementos;i++)
		{ 
			vRuta->numPuntosT+=vCuerpo[i].numP;
		}
		
		vRuta->octreeAnteriorActual=new PunteroBloque[2*vRuta->numPuntosT];
		return true;
	}
	if(vElementos<1)
	{
		return false;
	}
	return true;
};

Bloque CrearBloque(float vLimites[6]) // bloque corresponde a la estructura completa, subbloque corresponde a uno de los octrees de la seccion actual
{
	register Bloque vBloque;
	vBloque = new Octree;
	if (vBloque == NULL)
	{
		MessageBox::Show("no hay memoria....optimiza...");
	}
	vBloque->Padre=NULL;

	for(int i=0;i<8;i++)
	{
		vBloque->hijos[i]=NULL;
	}
	vBloque->raiz=true;
	vBloque->descendencia=false;
	vBloque->cuerposPresentes=NULL;		

	vBloque->recCuerposP=0;	
	vBloque->numPuntos=0;
	
	vBloque->numPartes=NULL;
	vBloque->nPoligonosPCuerpos=NULL;

	vBloque->PolListos=NULL;
	vBloque->IndicePolSubOctree=NULL;

	vBloque->minMax[0]=vLimites[0];
	vBloque->minMax[1]=vLimites[1];
	vBloque->minMax[2]=vLimites[2];
	vBloque->minMax[3]=vLimites[3];
	vBloque->minMax[4]=vLimites[4];
	vBloque->minMax[5]=vLimites[5];

	vBloque->medXYZ[0]=(vBloque->minMax[0]+vBloque->minMax[1])/(float)2.0; // punto medioX
	vBloque->medXYZ[1]=(vBloque->minMax[2]+vBloque->minMax[3])/(float)2.0; // punto medioY
	vBloque->medXYZ[2]=(vBloque->minMax[4]+vBloque->minMax[5])/(float)2.0; // punto medioZ

	return vBloque;
};

void InsertarSubBloques(PunteroBloque vPB,int vNumCuerpos)                                       // Se da puntero del bloque actual a dividir
{
	register int   j,i;
	register bool  x,y,z;
	x=y=z=false;
	register PunteroBloque vPSB;                                                // requeridos para la definicion de los 8 subbloques a generar
    vPSB=NULL;
   
	vPB->descendencia=true;
	for(i=0;i<8;i++)
	{
		vPSB = new Octree;

		if (vPSB == NULL)
		{
			MessageBox::Show("no hay memoria....optimiza...");
		}
		vPB->hijos[i]=vPSB;
		vPSB->Padre=vPB;

		vPSB->raiz=false;		
		vPSB->descendencia=false;
		vPSB->cuerposPresentes=new   bool[vNumCuerpos+1];
		vPSB->nPoligonosPCuerpos=new int[vNumCuerpos+1];
		for(j=0;j<=vNumCuerpos;j++)
		{
			vPSB->cuerposPresentes[j]=false;
			vPSB->nPoligonosPCuerpos[j]=0;
		}

		vPSB->recCuerposP=0;		
		vPSB->numPuntos=0;
		
		vPSB->numPartes=NULL;		

        vPSB->PolListos=NULL;
		vPSB->IndicePolSubOctree=NULL;

		z=(i>3)?1:0;
		y=(i==2 || i==3 || i==6 || i==7)?1:0;
		x=(i==1 || i==3 || i==5 || i==7)?1:0;
		
		vPSB->minMax[0]=(x)?vPB->medXYZ[0]:vPB->minMax[0];
		vPSB->minMax[1]=(x)?vPB->minMax[1]:vPB->medXYZ[0];
		vPSB->medXYZ[0]=(vPSB->minMax[0]+vPSB->minMax[1])/(float)2.0;

		vPSB->minMax[2]=(y)?vPB->medXYZ[1]:vPB->minMax[2];
		vPSB->minMax[3]=(y)?vPB->minMax[3]:vPB->medXYZ[1];
		vPSB->medXYZ[1]=(vPSB->minMax[2]+vPSB->minMax[3])/(float)2.0;

		vPSB->minMax[4]=(z)?vPB->medXYZ[2]:vPB->minMax[4];
		vPSB->minMax[5]=(z)?vPB->minMax[5]:vPB->medXYZ[2];
		vPSB->medXYZ[2]=(vPSB->minMax[4]+vPSB->minMax[5])/(float)2.0;

		for(j=0;j<8;j++)
		{
			vPSB->hijos[j]=NULL;
		}
	}
};

bool BorrarSubBloquesOctree(PunteroBloque vPB,int vNumCuerpos)
{
	if(!(vPB->raiz) && vPB!=NULL)
	{
		for(int i=0;i<8;i++)
		{
			delete[] vPB->hijos[i]->nPoligonosPCuerpos;

			delete[] vPB->hijos[i]->numPartes;
			delete[] vPB->hijos[i]->PolListos;
			if(vPB->hijos[i]->IndicePolSubOctree!=NULL)
			{
				for(i=1;i<=vNumCuerpos;i++)
				{
					delete[] vPB->hijos[i]->IndicePolSubOctree[i];
				}
				delete[]	vPB->hijos[i]->IndicePolSubOctree;
			}
			delete[] vPB->hijos[i]->cuerposPresentes;
			delete	 vPB->hijos[i];
			vPB->hijos[i]=NULL;
		}
		return true;
	}
	return false;
};

void DestruirBloque(Bloque vBloque, int vNumCuerpos) // destruir todo
{
	if(vBloque!=NULL)
	{
		register int i;
		register PunteroBloque vPB;
		
		vPB = vBloque;
		if(vPB->descendencia==true)
		{
			for(i=0;i<8;i++)
			{	
				DestruirBloque(vPB->hijos[i],vNumCuerpos);
				delete vPB->hijos[i];
			}
		}
		
		delete[]	vPB->numPartes;
		delete[]	vPB->nPoligonosPCuerpos;
		delete[]	vPB->PolListos;		
		
		if(vPB->IndicePolSubOctree!=NULL)
		{
			for(i=1;i<=vNumCuerpos;i++)
			{
				delete[] vPB->IndicePolSubOctree[i];
			}
			delete[]	vPB->IndicePolSubOctree;
		}
		delete[]	vPB->cuerposPresentes;
		if(vBloque->raiz)
		{
			delete vBloque;
		}
	}
};   


///////////////// Creacion de jerarquia de Octrees
bool	DesarrollarOctree(Bloque vOctree,RutaPuntos *vRuta,Cuerpo *vCuerpo,int vElementos,float vDXYZ[3],int vHaptico)
{
	register int	i,j,k,n,r,vertices,puntosCuerposAnt;
	register int	nCaras,nC;
	
	i=j=k=n=r=vertices=puntosCuerposAnt=0;

	PunteroBloque	vBloque,*vBloquesUsados;

	if(!CrearRuta(vRuta,vCuerpo,vElementos) || vOctree->raiz==false || vRuta->numPuntosT<=0)
	{
		return false;
	}

	nC=vRuta->numCuerpos;
	// Raiz posee todos los puntos....
	vOctree->numPuntos=vRuta->numPuntosT;
	vOctree->recCuerposP=nC;
	// Primera division arbitraria	
	DesarrollarHijos(vOctree,vRuta,vCuerpo,vDXYZ,vHaptico);

	// Determinar el numero de cuerpos en cada rama final y el numero de poligonos de cada uno de ellos
	for(i=1;i<=nC;i++) //for independiente.... hebras paralelizables..
	{
		if(vCuerpo[i].deseado && vCuerpo[i].existencia)
		{
			nCaras=vCuerpo[i].partes[0].numCaras;
			for(j=0;j<nCaras;j++) // for independiente...paralelizable... en fin cada punto de cada objeto se trata de forma independiente
			{
				vertices=vCuerpo[i].partes[0].malla[j].numVertices;
				vBloquesUsados= new PunteroBloque[vertices]; 
				for(k=0;k<vertices;k++)
				{
					vBloque=vRuta->octreeAnteriorActual[2*(puntosCuerposAnt+vCuerpo[i].partes[0].malla[j].indiceVertices[k])+0];
					vBloquesUsados[k]=vBloque;
					if(k==0)
					{
						vBloque->nPoligonosPCuerpos[i]++;
					}
					else
					{
						for(n=0;n<k;n++)
						{
							if(vBloque != vBloquesUsados[n])
							{
								vBloque->nPoligonosPCuerpos[i]++;
							}
						}
					}
				}
				delete[] vBloquesUsados;
			}
		}
		puntosCuerposAnt=puntosCuerposAnt+vCuerpo[i].numP;
	}

	// Asignacion Final y termino de la malla del Octree
	puntosCuerposAnt=0;
	for(i=1;i<=nC;i++) //for independiente.... hebras paralelizables..
	{
		if(vCuerpo[i].deseado && vCuerpo[i].existencia)
		{
			nCaras=vCuerpo[i].partes[0].numCaras;
			for(j=0;j<nCaras;j++) // for independiente...paralelizable... en fin cada punto de cada objeto se trata de forma independiente
			{
				vertices=vCuerpo[i].partes[0].malla[j].numVertices;
				vCuerpo[i].partes[0].malla[j].colision=false;
				vBloquesUsados= new PunteroBloque[vertices]; 
				for(k=0;k<vertices;k++)
				{
					vBloque=vRuta->octreeAnteriorActual[2*(puntosCuerposAnt+vCuerpo[i].partes[0].malla[j].indiceVertices[k])+0];
					vBloquesUsados[k]=vBloque;
					if(vBloque->IndicePolSubOctree==NULL)
					{
						vBloque->IndicePolSubOctree=	new int*[nC+1];
						vBloque->PolListos=				new	int[nC+1];

						for(n=1;n<=nC;n++)
						{
							vBloque->PolListos[n]=0;
							if(vCuerpo[i].deseado && vCuerpo[i].existencia)
							{
								if(vBloque->nPoligonosPCuerpos[n]>0)
								{
									vBloque->IndicePolSubOctree[n]=new int[vBloque->nPoligonosPCuerpos[n]];
								}
								else
								{
									vBloque->IndicePolSubOctree[n]=NULL;
								}
							}
						}
					}
					if(k==0)
					{
						vBloque->IndicePolSubOctree[i][vBloque->PolListos[i]]=j;
						vBloque->PolListos[i]++;
					}
					else
					{
						for(n=0;n<k;n++)
						{
							if(vBloque != vBloquesUsados[n])
							{
								vBloque->IndicePolSubOctree[i][vBloque->PolListos[i]]=j;
								vBloque->PolListos[i]++;
							}
						}
					}
				}
				delete[] vBloquesUsados;
			}
		}
		puntosCuerposAnt=puntosCuerposAnt+vCuerpo[i].numP;
	}
	return true;
};

bool DesarrollarHijos(Bloque vSubOctree,RutaPuntos *vRuta,Cuerpo *vCuerpo,float vDXYZ[3],int vHaptico) // Asigna un vector con la referencia de a donde va cada punto
{
	register bool	cP=false;
	register bool	condE,condH;
	register int	i,j,repetidos,x,y,z,indice,nP,nC,puntoActual,puntoActualResto,indicePorHijo[8];
	indicePorHijo[0]=indicePorHijo[1]=indicePorHijo[2]=indicePorHijo[3]=indicePorHijo[4]=indicePorHijo[5]=indicePorHijo[6]=indicePorHijo[7]=0;

	i=j=repetidos=0;
    nC=vRuta->numCuerpos;
	register int*	nPuntos;
	nPuntos=new int[nC+1];
	InsertarSubBloques(vSubOctree,nC);

	condE=vCuerpo[0].existencia;

	puntoActualResto=0;
	if(vSubOctree->raiz)
	{
		for(i=1;i<=nC;i++) //for independiente.... hebras paralelizables..
		{
			puntoActual=0;
			nPuntos[i]=0;
			if(vCuerpo[i].deseado && vCuerpo[i].existencia)
			{
				condH=condE&&(i==vHaptico);
				nP=3*vCuerpo[i].numP;
				for(j=0;j<nP;j=j+3,puntoActual=puntoActual+2) // for independiente...paralelizable... en fin cada punto de cada objeto se trata de forma independiente
				{
					x=(vCuerpo[condH?0:i].verPuntos[j+0]>=vSubOctree->medXYZ[0])?1:0;
					y=(vCuerpo[condH?0:i].verPuntos[j+1]>=vSubOctree->medXYZ[1])?1:0;
					z=(vCuerpo[condH?0:i].verPuntos[j+2]>=vSubOctree->medXYZ[2])?1:0;
					indice=x+2*y+4*z;
					vRuta->octreeAnteriorActual[(puntoActualResto+puntoActual)+0]=vSubOctree->hijos[indice];
					indicePorHijo[indice]++; // da el numero de puntos que manejaran cada hijo... esto debe ser sincronizado
					if(!vSubOctree->hijos[indice]->cuerposPresentes[i])
					{	
						nPuntos[i]=vCuerpo[i].numP;
						vSubOctree->hijos[indice]->cuerposPresentes[i]=true;
						vSubOctree->hijos[indice]->recCuerposP++;
					}
				}
			}
			puntoActualResto=puntoActualResto+(int)(2*vCuerpo[i].numP);
		}
	}
	else
	{
		for(i=1;i<=nC;i++) //for independiente.... hebras paralelizables..
		{
			puntoActual=0;
			nPuntos[i]=0;
			if(vCuerpo[i].deseado && vCuerpo[i].existencia)
			{
				condH=condE&&(i==vHaptico);
				nP=3*vCuerpo[i].numP;                                  
				for(j=0;j<nP;j=j+3,puntoActual=puntoActual+2) // for independiente...paralelizable... en fin cada punto de cada objeto se trata de forma independiente
				{
                    // Cambiar a Paralelizable MDUI multiple data unique instruction o algo asi que a esta hora no me acuerdo...
					if(vRuta->octreeAnteriorActual[(puntoActualResto+puntoActual)+0]==vSubOctree) // seria mejor dividir los puntos por cada bloquey asi cada quien se ocupa de los suyo ..en vez de revizar todo...evaluar si es factible en ccomparacion con la asignacion de memoria de esta data extra
					{
						x=(vCuerpo[condH?0:i].verPuntos[j+0]>=vSubOctree->medXYZ[0])?1:0;
						y=(vCuerpo[condH?0:i].verPuntos[j+1]>=vSubOctree->medXYZ[1])?1:0;
						z=(vCuerpo[condH?0:i].verPuntos[j+2]>=vSubOctree->medXYZ[2])?1:0;
						indice=x+2*y+4*z;
						vRuta->octreeAnteriorActual[puntoActualResto+puntoActual+0]=vSubOctree->hijos[indice];
						indicePorHijo[indice]++; // da el numero de puntos que manejaran cada hijo... esto debe ser sincronizado
						repetidos++; // indice por hijo indica los puntos asignados a cada subBloque
						if(!vSubOctree->hijos[indice]->cuerposPresentes[i])
						{	
							nPuntos[i]=vCuerpo[i].numP;
							vSubOctree->hijos[indice]->cuerposPresentes[i]=true;
							vSubOctree->hijos[indice]->recCuerposP++;
						}
					}
				}
			}
			puntoActualResto=puntoActualResto+(int)(2*vCuerpo[i].numP);
		}
	}
	
	for(i=0;i<8;i++) // nuevamente cada subnivel es independiente..aunque operan sobre datos compartidos pero solo afectan su porcion...
	{
		vSubOctree->hijos[i]->numPuntos=indicePorHijo[i];		
		for(j=1;j<=nC;j++)
		{
			cP= (nPuntos[j]>0 && indicePorHijo[i]>vRuta->factorG*nPuntos[j]);
			j=(cP)?nC+1:j;
		}
		if((indicePorHijo[i]>0) &&(cP) && (indicePorHijo[i]!=repetidos || vRuta->factorR) && (indicePorHijo[i]>vRuta->factorU) && ( (		(vSubOctree->hijos[i]->minMax[1]-vSubOctree->hijos[i]->minMax[0])>vRuta->factorR*vDXYZ[0])&&((vSubOctree->hijos[i]->minMax[3]-vSubOctree->hijos[i]->minMax[2])>vRuta->factorR*vDXYZ[1])&&((vSubOctree->hijos[i]->minMax[5]-vSubOctree->hijos[i]->minMax[4])>vRuta->factorR*vDXYZ[2]) ) )
		{
			DesarrollarHijos(vSubOctree->hijos[i],vRuta,vCuerpo,vDXYZ,vHaptico);		
		}
	}
	delete[] nPuntos;
	return true;
}


//// Calculo de Colisiones en un Octree

bool	ColisionarOctree(Bloque vOctree,RutaPuntos *vRuta,Cuerpo *vCuerpo,int vHaptico)
{
	if(vOctree!=NULL)
	{
		register int	i,j,k,nP,nC,j2,k2,nP2,indiceP[3],indiceP2[3];
		register float	factor=2;
		register float	triaA[3][3],triaB[3][3],dMinMax[3];
		register bool	s=false;
		register bool   condE,condH;
		nC=vRuta->numCuerpos;

		condE=vCuerpo[0].existencia;

		for(i=0;i<8;i++) // nuevamente cada subnivel es independiente..aunque operan sobre datos compartidos pero solo afectan su porcion...
		{
			if(vOctree->hijos[i]->recCuerposP>1)
			{
				if(vOctree->hijos[i]->descendencia)
				{
					ColisionarOctree(vOctree->hijos[i],vRuta,vCuerpo,vHaptico);
				}
				else
				{
					dMinMax[0]=vOctree->hijos[i]->minMax[1] - vOctree->hijos[i]->minMax[0];
					dMinMax[1]=vOctree->hijos[i]->minMax[3] - vOctree->hijos[i]->minMax[2];
					dMinMax[2]=vOctree->hijos[i]->minMax[5] - vOctree->hijos[i]->minMax[4];

					for(j=1;j<=nC;j++)
					{
						condH=condE&&(j==vHaptico);
						if(vOctree->hijos[i]->cuerposPresentes[j])
						{
							nP=vOctree->hijos[i]->nPoligonosPCuerpos[j];
							for(k=0;k<nP;k++)
							{
								indiceP[0]=3*vCuerpo[condH?0:j].partes[0].malla[vOctree->hijos[i]->IndicePolSubOctree[j][k]].indiceVertices[0];
								indiceP[1]=3*vCuerpo[condH?0:j].partes[0].malla[vOctree->hijos[i]->IndicePolSubOctree[j][k]].indiceVertices[1];
								indiceP[2]=3*vCuerpo[condH?0:j].partes[0].malla[vOctree->hijos[i]->IndicePolSubOctree[j][k]].indiceVertices[2];

								triaA[0][0]=vCuerpo[condH?0:j].verPuntos[indiceP[0]+0];	//	Primer vertice..X
								triaA[0][1]=vCuerpo[condH?0:j].verPuntos[indiceP[0]+1];	//	Primer vertice..Y
								triaA[0][2]=vCuerpo[condH?0:j].verPuntos[indiceP[0]+2];	//	Primer vertice..Z

								triaA[1][0]=vCuerpo[condH?0:j].verPuntos[indiceP[1]+0];	//	Sec vertice..X
								triaA[1][1]=vCuerpo[condH?0:j].verPuntos[indiceP[1]+1];	//	 vertice..Y
								triaA[1][2]=vCuerpo[condH?0:j].verPuntos[indiceP[1]+2];	//	 vertice..Z

								triaA[2][0]=vCuerpo[condH?0:j].verPuntos[indiceP[2]+0];	//	Tercer vertice..X
								triaA[2][1]=vCuerpo[condH?0:j].verPuntos[indiceP[2]+1];	//	 vertice..Y
								triaA[2][2]=vCuerpo[condH?0:j].verPuntos[indiceP[2]+2];	//	 vertice..Z

								// Comparar con los otros poligonos
								for(j2=j+1;j2<=nC;j2++)
								{
									if(vOctree->hijos[i]->cuerposPresentes[j2])
									{
										nP2=vOctree->hijos[i]->nPoligonosPCuerpos[j2];
										for(k2=0;k2<nP2;k2++)
										{
											indiceP2[0]=3*vCuerpo[j2].partes[0].malla[vOctree->hijos[i]->IndicePolSubOctree[j2][k2]].indiceVertices[0];
											indiceP2[1]=3*vCuerpo[j2].partes[0].malla[vOctree->hijos[i]->IndicePolSubOctree[j2][k2]].indiceVertices[1];
											indiceP2[2]=3*vCuerpo[j2].partes[0].malla[vOctree->hijos[i]->IndicePolSubOctree[j2][k2]].indiceVertices[2];

											triaB[0][0]=vCuerpo[j2].verPuntos[indiceP2[0]+0];	//	T2 Primer vertice..X
											triaB[0][1]=vCuerpo[j2].verPuntos[indiceP2[0]+1];	//	T2 Primer vertice..Y
											triaB[0][2]=vCuerpo[j2].verPuntos[indiceP2[0]+2];	//	T2 Primer vertice..Z

											triaB[1][0]=vCuerpo[j2].verPuntos[indiceP2[1]+0];	//	T2 Sec vertice..X
											triaB[1][1]=vCuerpo[j2].verPuntos[indiceP2[1]+1];	//	 T2 vertice..Y
											triaB[1][2]=vCuerpo[j2].verPuntos[indiceP2[1]+2];	//	 vertice..Z

											triaB[2][0]=vCuerpo[j2].verPuntos[indiceP2[2]+0];	//	T2 Tercer vertice..X
											triaB[2][1]=vCuerpo[j2].verPuntos[indiceP2[2]+1];	//	 vertice..Y
											triaB[2][2]=vCuerpo[j2].verPuntos[indiceP2[2]+2];	//	 vertice..Z
											//if(ColisionTT(triaA,triaB))

												if( 
((factor*fabs(triaA[0][0]-triaB[0][0])<dMinMax[0]) && (factor*fabs(triaA[0][1]-triaB[0][1])<dMinMax[1]) && (factor*fabs(triaA[0][2]-triaB[0][2])<dMinMax[2]))
||((factor*fabs(triaA[0][0]-triaB[1][0])<dMinMax[0]) && (factor*fabs(triaA[0][1]-triaB[1][1])<dMinMax[1]) && (factor*fabs(triaA[0][2]-triaB[1][2])<dMinMax[2]))
||((factor*fabs(triaA[0][0]-triaB[2][0])<dMinMax[0]) && (factor*fabs(triaA[0][1]-triaB[2][1])<dMinMax[1]) && (factor*fabs(triaA[0][2]-triaB[2][2])<dMinMax[2]))
||
((factor*fabs(triaA[1][0]-triaB[0][0])<dMinMax[0]) && (factor*fabs(triaA[1][1]-triaB[0][1])<dMinMax[1]) && (factor*fabs(triaA[1][2]-triaB[0][2])<dMinMax[2]))
||((factor*fabs(triaA[1][0]-triaB[1][0])<dMinMax[0]) && (factor*fabs(triaA[1][1]-triaB[1][1])<dMinMax[1]) && (factor*fabs(triaA[1][2]-triaB[1][2])<dMinMax[2]))
||((factor*fabs(triaA[1][0]-triaB[2][0])<dMinMax[0]) && (factor*fabs(triaA[1][1]-triaB[2][1])<dMinMax[1]) && (factor*fabs(triaA[1][2]-triaB[2][2])<dMinMax[2]))
||
((factor*fabs(triaA[2][0]-triaB[0][0])<dMinMax[0]) && (factor*fabs(triaA[2][1]-triaB[0][1])<dMinMax[1]) && (factor*fabs(triaA[2][2]-triaB[0][2])<dMinMax[2]))
||((factor*fabs(triaA[2][0]-triaB[1][0])<dMinMax[0]) && (factor*fabs(triaA[2][1]-triaB[1][1])<dMinMax[1]) && (factor*fabs(triaA[2][2]-triaB[1][2])<dMinMax[2]))
||((factor*fabs(triaA[2][0]-triaB[2][0])<dMinMax[0]) && (factor*fabs(triaA[2][1]-triaB[2][1])<dMinMax[1]) && (factor*fabs(triaA[2][2]-triaB[2][2])<dMinMax[2]))
													)
											{
												vCuerpo[j].partes[0].malla[vOctree->hijos[i]->IndicePolSubOctree[j][k]].colision=true;
												vCuerpo[j2].partes[0].malla[vOctree->hijos[i]->IndicePolSubOctree[j2][k2]].colision=true;
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	return false;
}

bool	ActualizarOctree(Bloque vOctree,RutaPuntos *vRuta,Cuerpo *vCuerpo)
{
	//register int	i,j,x,y,z,indice,nP,nC,puntoActual,puntoActualResto,indicePorHijo[8];
	//indicePorHijo[0]=indicePorHijo[1]=indicePorHijo[2]=indicePorHijo[3]=indicePorHijo[4]=indicePorHijo[5]=indicePorHijo[6]=indicePorHijo[7]=0;

	//i=j=0;
 //   nC=vRuta->numCuerpos;
	//register int*	nPuntos;
	//nPuntos=new int[nC+1];

	//puntoActualResto=0;

	//puntoActual=0;
	//nPuntos[i]=0;
	//if(vCuerpo[i].deseado && vCuerpo[i].existencia)
	//{
	//	nP=3*vCuerpo[i].numP;                                  
	//	for(j=0;j<nP;j=j+3,puntoActual=puntoActual+2) // for independiente...paralelizable... en fin cada punto de cada objeto se trata de forma independiente
	//	{
 //           // Cambiar a Paralelizable MDUI multiple data unique instruction o algo asi que a esta hora no me acuerdo...
	//		if(vRuta->octreeAnteriorActual[(puntoActualResto+puntoActual)+0]==vSubOctree) // seria mejor dividir los puntos por cada bloquey asi cada quien se ocupa de los suyo ..en vez de revizar todo...evaluar si es factible en ccomparacion con la asignacion de memoria de esta data extra
	//		{
	//			x=(vCuerpo[condH?0:i].verPuntos[j+0]>=vSubOctree->medXYZ[0])?1:0;
	//			y=(vCuerpo[condH?0:i].verPuntos[j+1]>=vSubOctree->medXYZ[1])?1:0;
	//			z=(vCuerpo[condH?0:i].verPuntos[j+2]>=vSubOctree->medXYZ[2])?1:0;
	//			indice=x+2*y+4*z;
	//			vRuta->octreeAnteriorActual[puntoActualResto+puntoActual+0]=vSubOctree->hijos[indice];
	//			indicePorHijo[indice]++; // da el numero de puntos que manejaran cada hijo... esto debe ser sincronizado
	//			repetidos++; // indice por hijo indica los puntos asignados a cada subBloque
	//			if(!vSubOctree->hijos[indice]->cuerposPresentes[i])
	//			{	
	//				nPuntos[i]=vCuerpo[i].numP;
	//				vSubOctree->hijos[indice]->cuerposPresentes[i]=true;
	//				vSubOctree->hijos[indice]->recCuerposP++;
	//			}
	//		}
	//	}
	//}
	//puntoActualResto=puntoActualResto+(int)(2*vCuerpo[i].numP);

	return true;
}

////////////////////////////////////////////////////////
bool	DibujarOctree(Bloque vOctree)
{
	if(vOctree!=NULL)
	{
		if(vOctree->descendencia)
		{
			DibujarBloque(vOctree);
			for(register int i=0;i<8;i++)
			{
				DibujarOctree(vOctree->hijos[i]);
			}
			return true;
		}
		else if(vOctree->recCuerposP>0)
		{
			DibujarBloque(vOctree);		
		}
	}
	return false;
}

bool	DibujarBloque(Bloque vBloque)
{
    register float minMax[6];
    minMax[0]=vBloque->minMax[0];
    minMax[1]=vBloque->minMax[1];
    minMax[2]=vBloque->minMax[2];
    minMax[3]=vBloque->minMax[3];
    minMax[4]=vBloque->minMax[4];
    minMax[5]=vBloque->minMax[5];
    
	glColor3d(0.0,0.0,0.0);

	glBegin(GL_POLYGON);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[2],vBloque->minMax[4]);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[3],vBloque->minMax[4]);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[3],vBloque->minMax[4]);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[2],vBloque->minMax[4]);
	glEnd();
	glBegin(GL_POLYGON);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[2],vBloque->minMax[4]);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[3],vBloque->minMax[4]);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[3],vBloque->minMax[5]);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[2],vBloque->minMax[5]);
	glEnd();
	glBegin(GL_POLYGON);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[2],vBloque->minMax[5]);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[3],vBloque->minMax[5]);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[3],vBloque->minMax[5]);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[2],vBloque->minMax[5]);
	glEnd();
	glBegin(GL_POLYGON);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[2],vBloque->minMax[5]);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[3],vBloque->minMax[5]);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[3],vBloque->minMax[4]);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[2],vBloque->minMax[4]);
	glEnd();

	glBegin(GL_POLYGON);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[3],vBloque->minMax[4]);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[3],vBloque->minMax[5]);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[3],vBloque->minMax[5]);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[3],vBloque->minMax[4]);
	glEnd();
	glBegin(GL_POLYGON);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[3],vBloque->minMax[4]);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[3],vBloque->minMax[4]);
		glVertex3f(vBloque->minMax[1],vBloque->minMax[3],vBloque->minMax[5]);
		glVertex3f(vBloque->minMax[0],vBloque->minMax[3],vBloque->minMax[5]);
	glEnd();
	return true;
}
