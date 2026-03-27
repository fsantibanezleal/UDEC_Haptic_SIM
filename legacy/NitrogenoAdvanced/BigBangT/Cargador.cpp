//---------------------------------------------------------------------------
#pragma once
#pragma hdrstop

#include <windows.h>
#include <stdio.h>

#include "Cargador.h"

using namespace System;
using namespace System::Windows::Forms;
using namespace System::Globalization;

//---------------------------------------------------------------------------

bool	Cargador::CargadorDeFichero(Cuerpo *vCuerpo, System::Windows::Forms::TextBox ^vTexto,int vTipo)
{
	CultureInfo^ cultura = gcnew CultureInfo("en-US"); // Empleado en el uso de metodos Parse

	register int	espacios[100];
	register int	barras[100];
	register int	j=0;
	register int	v=0;
	register int	vt=0;
	register int	vn=0;
	register int	f=0;
	register int	linea=0;
	register int	actual=0;
	register int	vertice=0;
	register int	numBarras=0; // Arreglar para seleccion de subobjetos
	register int	largoT,largoL,indice;

	register float	puntos[3][3];

	register String^ temp;
	register String^ subTemp;
	register array<String^>^ texto= gcnew array<String^>( vTexto->Lines->Length );
	register char	noUsad[10],tempLineaChar[300];
	texto=vTexto->Lines;
	largoT=texto->Length;

	vCuerpo->texturas=false;
	vCuerpo->normales=false;

	if(vTipo==0)
	{
		for(linea=0;linea<largoT;linea++)
		{
			temp=texto[linea];
			largoL=temp->Length;

			if(largoL>2)
			{
				subTemp=temp->Substring(0,2);
				if(subTemp=="v ")	
				{
					v++;
				}
				else if( subTemp=="vt")	
				{
					vt++;
				}
				else if( subTemp=="vn")	
				{
					vn++;
				}

				else if( subTemp=="f ")	
				{
					f++;
				}
				//else if( subTemp=="g ")	
				//{
				//	vCuerpo->numG++;
				//}
			}
		}
		
		vCuerpo->numP=v;
		vCuerpo->numN=vn;
		vCuerpo->numT=vt;

		if(v==0 || f==0)
		{
			return 0;
			MessageBox::Show("No hay vertices o Caras... ");
		}

		vCuerpo->deseado=true;
		vCuerpo->existencia=true;
		vCuerpo->numG=1; // lo general.. no hay utilidad momentanea de implementacion
		vCuerpo->verPuntos= new float[3*v];

		if(vn>0)
		{
			vCuerpo->normales=true;
			vCuerpo->verNormales= new float[3*vn];
		}

		if(vt>0)
		{
			vCuerpo->texturas=true;		
			vCuerpo->verTexturas= new float[3*vt];
		}

		vCuerpo->partes= new MalladoReferido[1]; // 1 G por defecto
		vCuerpo->partes[0].deseado=true;
		vCuerpo->partes[0].numCaras=f;
		vCuerpo->partes[0].malla= new PoligonoReferido[f]; 
		vCuerpo->pivote[0]=vCuerpo->pivote[1]=vCuerpo->pivote[2]=0.0;
		v=vt=vn=f=0;

		for(linea=0;linea<largoT;linea++)
		{
			temp=texto[linea];
			largoL=temp->Length;
			for(j=0;j<largoL;j++)
			{
				tempLineaChar[j]=(int)temp[j];
			}
			tempLineaChar[largoL]=' ';
			if(largoL>2)
			{
				subTemp=temp->Substring(0,2);
				if( subTemp=="v ")
				{
					sscanf(tempLineaChar,"%1s %f %f %f",noUsad,&vCuerpo->verPuntos[3*v+0],&vCuerpo->verPuntos[3*v+1],&vCuerpo->verPuntos[3*v+2]);
					v++;
				}
				else if( subTemp=="vt")
				{
					sscanf(tempLineaChar,"%2s %f %f %f",noUsad,&vCuerpo->verTexturas[3*vt+0],&vCuerpo->verTexturas[3*vt+1],&vCuerpo->verTexturas[3*vt+2]);
					vt++;
				}
				else if( subTemp=="vn")
				{
					sscanf(tempLineaChar,"%2s %f %f %f",noUsad,&vCuerpo->verNormales[3*vn+0],&vCuerpo->verNormales[3*vn+1],&vCuerpo->verNormales[3*vn+2]);
					vn++;
				}
				else if( subTemp=="f ")
				{
					numBarras=0;
					if(vCuerpo->texturas || vCuerpo->normales)
					{
						while(1)
						{
							barras[numBarras]=temp->IndexOf("/",(numBarras-1<0)?0:barras[numBarras-1]+1);
							if(barras[numBarras]==-1)
							{
								break;
							}
							numBarras++;
						}
					}

					actual=0;
					while(1)
					{
						espacios[actual]=temp->IndexOf(" ",(actual-1<0)?0:espacios[actual-1]+1);
						if(espacios[actual]<largoL)
						{
							while(temp->Substring(espacios[actual]+1,1)==" ")
							{
								espacios[actual]++;
							}
						}

						if(espacios[actual]==-1)
						{
							break;
						}
						actual++;
					}

					vCuerpo->partes[0].malla[f].numVertices=actual;
					if(actual>20)
					{
						int asd=3;
					}

					vCuerpo->partes[0].malla[f].indiceVertices= new int[actual];

					if(vCuerpo->texturas)
					{
						vCuerpo->partes[0].malla[f].indiceTexturas= new int[actual];
					}
					if(vCuerpo->normales)
					{
						vCuerpo->partes[0].malla[f].indiceNormales= new int[actual];
					}
					
					for(vertice=0;vertice<actual;vertice++)
					{
						if(vCuerpo->texturas || vCuerpo->normales)
						{
							indice=int::Parse(temp->Substring(espacios[vertice]+1,barras[2*vertice]-espacios[vertice]-1),cultura)-1;
							vCuerpo->partes[0].malla[f].indiceVertices[vertice]=abs(indice);
						}
						else
						{
							if(espacios[vertice+1]==-1)
							{
								indice=int::Parse(temp->Substring(espacios[vertice]+1),cultura)-1;
								vCuerpo->partes[0].malla[f].indiceVertices[vertice]=abs(indice);
							}
							else
							{
								indice=int::Parse(temp->Substring(espacios[vertice]+1,espacios[vertice+1]-espacios[vertice]-1),cultura)-1;
								vCuerpo->partes[0].malla[f].indiceVertices[vertice]=abs(indice);
							}
						}

						if(vCuerpo->texturas)
						{
							vCuerpo->partes[0].malla[f].indiceTexturas[vertice]=abs(int::Parse(temp->Substring(barras[2*vertice]+1,barras[2*vertice+1]-barras[2*vertice]-1),cultura)-1);
						}
						
						if(vCuerpo->normales)
						{
							if(espacios[vertice+1]==-1)
							{
								vCuerpo->partes[0].malla[f].indiceNormales[vertice]=abs(int::Parse(temp->Substring(barras[2*vertice+1]+1),cultura)-1);
							}
							else
							{
								vCuerpo->partes[0].malla[f].indiceNormales[vertice]=abs(int::Parse(temp->Substring(barras[2*vertice+1]+1,espacios[vertice+1]-barras[2*vertice+1]-1),cultura)-1);							
							}
						}
						// Asignar Normales
						if(vertice <3)
						{
							puntos[vertice][0]=vCuerpo->verPuntos[indice+0];
							puntos[vertice][1]=vCuerpo->verPuntos[indice+1];
							puntos[vertice][2]=vCuerpo->verPuntos[indice+2];
							if(vertice==2)
							{
								NormalP(&vCuerpo->partes[0].malla[f],puntos[0],puntos[1],puntos[2]);	
							}
						}
					}
					vCuerpo->partes[0].malla[f].colision=false;
					f++;	
				}
				//else if( subTemp=="g ")v
				//{
				//}
			}
		}
		if(vCuerpo->deseado==false || vCuerpo->partes[0].deseado==false)
		{
			delete cultura;
			delete[] texto;
			return false;
		}
		vCuerpo->vXYZ[0]=vCuerpo->vXYZ[1]=vCuerpo->vXYZ[2]=(float)0.0;
	}
	delete cultura;
	delete[] texto;
	return true;
};