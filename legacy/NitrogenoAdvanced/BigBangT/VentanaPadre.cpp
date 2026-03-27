//---------------------------------------------------------------------------
#pragma once
#pragma hdrstop

#include "VentanaPadre.h"

//---------------------------------------------------------------------------

bool	volver,externo;
int		w1,h1;

void BigBangT::VentanaPadre::Inicio(void)
{
	volver=externo=false;

	Dibujante.Actuador.hrc2=wglCreateContext(GetDC((HWND) ventanaCentral.Handle.ToPointer()));
	Dibujante.Actuador.VentanaCreate2( reinterpret_cast<HWND> (ventanaCentral.Handle.ToPointer()));

	Dibujante.Actuador.hrc=wglCreateContext(GetDC((HWND) PanelG->Handle.ToPointer()));
	Dibujante.Actuador.VentanaCreate( reinterpret_cast<HWND> (PanelG->Handle.ToPointer()));

	Dibujante.numObjetosAUsar=10;
	Dibujante.numObjetosEstablecidos=0;
	Dibujante.Objetos= new Cuerpo[Dibujante.numObjetosAUsar+1];
	for(register GLuint j=0;j<Dibujante.numObjetosAUsar+1;j++)
	{
		Dibujante.Objetos[j].existencia=false;
	}
	Dibujante.octreePrincipal=NULL;
	Dibujante.Inicializar();
	factorEscala=new float[3];
	factorEscala[0]=factorEscala[1]=factorEscala[2]=2.0;
	dX=dY=dZ=5;
	rotX=rotY=rotZ=20;
	signRotacion=1;

	actListo=true;

	Dibujante.rehacerDibujo=true;

	cD->AllowFullOpen=true;
	miM=gcnew Mutex;
};

void BigBangT::VentanaPadre::VentanaPadre_Paint(System::Object^  sender, System::Windows::Forms::PaintEventArgs^  e) 
{ 
//
};

System::Void BigBangT::VentanaPadre::PanelG_Paint(System::Object^  sender, System::Windows::Forms::PaintEventArgs^  e) 
{
//
};

System::Void BigBangT::VentanaPadre::PanelG_DoubleClick(System::Object^  sender, System::EventArgs^  e)
{
	if(miM->WaitOne())
	{
		externo=true;

		w1=PanelG->Width;
		h1=PanelG->Height;

		Dibujante.Actuador.SetCurrentWindow2();
		Dibujante.Resize(ventanaCentral.Width,ventanaCentral.Height);
		ventanaCentral.Show();

		miM->ReleaseMutex();
	}
};

System::Void BigBangT::VentanaPadre::VentanaPadre_Resize(System::Object^  sender, System::EventArgs^  e)
{
	Dibujante.rehacerDibujo=true;
	Dibujante.Resize(PanelG->Width,PanelG->Height);
};

System::Void BigBangT::VentanaPadre::MenuCerrar_Click(System::Object^  sender, System::EventArgs^  e) 
{
	exit(1);
};

System::Void BigBangT::VentanaPadre::MenuAbrir_Click(System::Object^  sender, System::EventArgs^  e) 
{
	Dibujante.rehacerDibujo=true;
	if ( AbrirFile->ShowDialog() == System::Windows::Forms::DialogResult::OK )
	{
		int ultimoP=AbrirFile->FileName->LastIndexOf(".");
		if(AbrirFile->FileName->Substring(ultimoP)==".obj" )
		{
			if(Dibujante.numObjetosEstablecidos<Dibujante.numObjetosAUsar && Dibujante.numObjetosAUsar!=0)
			{
				Memo->Text= File::ReadAllText(AbrirFile->FileName);

				if(Carguero.CargadorDeFichero(&Dibujante.Objetos[Dibujante.numObjetosEstablecidos+1],Memo,0))
				{
					Dibujante.numObjetosEstablecidos++;
					Dibujante.rehacerDibujo=true;
				}
				else
				{
					MessageBox::Show("Archivo no Utilizable");
				}
				Memo->Clear();
			}
		}
	}
};

System::Void BigBangT::VentanaPadre::VentanaPadre_KeyDown(System::Object^  sender, System::Windows::Forms::KeyEventArgs^  e)
{
	switch (e->KeyCode) 
	{
	// Acciones sobre objetos
		case Keys::Add: // Ampliar Objeto
		{
			CuerpoEscalar(&Dibujante.Objetos[Dibujante.indiceObjetoActivo],factorEscala,Dibujante.Objetos[Dibujante.indiceObjetoActivo].pivote);
			actualizacion=true;
			break;
		}
		case Keys::Subtract: // Reducir Objeto
		{
			register float temp[3];
			temp[0]=(float)(1.0/factorEscala[0]);
			temp[1]=(float)(1.0/factorEscala[1]);
			temp[2]=(float)(1.0/factorEscala[2]);

			CuerpoEscalar(&Dibujante.Objetos[Dibujante.indiceObjetoActivo],temp,Dibujante.Objetos[Dibujante.indiceObjetoActivo].pivote);
			actualizacion=true;
			break;
		}
		case Keys::Return: // Cambiar de Objeto
		{
			Dibujante.indiceObjetoActivo=Dibujante.SelecObjeto(Dibujante.indiceObjetoActivo+1);
			break;
		}
		case Keys::NumPad9 : // Desplazar en +x
		{
			CuerpoTrasladar(&Dibujante.Objetos[Dibujante.indiceObjetoActivo],dX,0,0);
			actualizacion=true;
			break;
		}
		case Keys::NumPad8 : // Desplazar en -x
		{
			CuerpoTrasladar(&Dibujante.Objetos[Dibujante.indiceObjetoActivo],-dX,0,0);
			actualizacion=true;
			break;
		}
		case Keys::NumPad6 : // Desplazar en +y
		{
			CuerpoTrasladar(&Dibujante.Objetos[Dibujante.indiceObjetoActivo],0,dY,0);
			actualizacion=true;
			break;
		}
		case Keys::NumPad5 : // Desplazar en -y
		{
			CuerpoTrasladar(&Dibujante.Objetos[Dibujante.indiceObjetoActivo],0,-dY,0);
			actualizacion=true;
			break;
		}
		case Keys::NumPad3 : // Desplazar en +z
		{
			CuerpoTrasladar(&Dibujante.Objetos[Dibujante.indiceObjetoActivo],0,0,dZ);
			actualizacion=true;
			break;
		}
		case Keys::NumPad2 : // Desplazar en -z
		{
			CuerpoTrasladar(&Dibujante.Objetos[Dibujante.indiceObjetoActivo],0,0,-dZ);
			actualizacion=true;
			break;
		}
		case Keys::NumPad0 : // Cambiar sentido rotacion
		{
			signRotacion*=-1;
			break;
		}
		case Keys::NumPad7 : // Rotar en X
		{
			register float temp[3];
			temp[1]=temp[2]=0.0;
			temp[0]=signRotacion*rotX;
			CuerpoRotar(&Dibujante.Objetos[Dibujante.indiceObjetoActivo],temp,Dibujante.Objetos[Dibujante.indiceObjetoActivo].pivote);
			actualizacion=true;
			break;
		}
		case Keys::NumPad4 : // Rotar en Y
		{
			register float temp[3];
			temp[0]=temp[2]=0.0;
			temp[1]=signRotacion*rotY;
			CuerpoRotar(&Dibujante.Objetos[Dibujante.indiceObjetoActivo],temp,Dibujante.Objetos[Dibujante.indiceObjetoActivo].pivote);
			actualizacion=true;
			break;
		}
		case Keys::NumPad1 : // Rotar en Z
		{
			register float temp[3];
			temp[0]=temp[1]=0.0;
			temp[2]=signRotacion*rotZ;
			CuerpoRotar(&Dibujante.Objetos[Dibujante.indiceObjetoActivo],temp,Dibujante.Objetos[Dibujante.indiceObjetoActivo].pivote);
			actualizacion=true;
			break;
		}

	// Acciones sobre entorno
		case Keys::F1 : // -dX
		{
			Dibujante.visualT[0]-=(float)2;
			Dibujante.rehacerDibujo=true;
			break;
		}
		case Keys::F2 : // dX
		{
			Dibujante.visualT[0]+=(float)2;
			Dibujante.rehacerDibujo=true;
			break;
		}
		case Keys::F3 : // -dY
		{
			Dibujante.visualT[1]-=(float)2;
			Dibujante.rehacerDibujo=true;
			break;
		}
		case Keys::F4 : // dY
		{
			Dibujante.visualT[1]+=(float)2;
			Dibujante.rehacerDibujo=true;
			break;
		}
		case Keys::F5 : // -dZ
		{
			Dibujante.visualT[2]-=(float)2;
			Dibujante.rehacerDibujo=true;
			break;
		}
		case Keys::F6 : // dZ
		{
			Dibujante.visualT[2]+=(float)2;
			Dibujante.rehacerDibujo=true;
			break;
		}
		case Keys::F7 : // rX
		{
			Dibujante.visualR[0]+=(float)15*signRotacion;
			Dibujante.rehacerDibujo=true;
			break;
		}
		case Keys::F8 : // rY
		{
			Dibujante.visualR[1]+=(float)15*signRotacion;
			Dibujante.rehacerDibujo=true;
			break;
		}
		case Keys::F9 : // rZ
		{
			Dibujante.visualR[2]+=(float)15*signRotacion;
			Dibujante.rehacerDibujo=true;
			break;
		}
	// Funciones de elementos de Colision

		case Keys::Space : // Cambiar de Objeto controlado por haptico
		{
			if(Dibujante.superHaptico->creacion && Dibujante.superHaptico->habilitado)
			{
				Dibujante.indiceObjetoHaptico=Dibujante.SelecObjeto(Dibujante.indiceObjetoHapticoAnt+1);
			}
			break;
		}

		case Keys::F11 : // Creacion Octree
		{
			Dibujante.dibOctree=!Dibujante.dibOctree;
			break;
		}
		case Keys::Escape : // Creacion Octree
		{
			if(Dibujante.octreePrincipal!=NULL)
			{
				DestruirBloque(Dibujante.octreePrincipal,Dibujante.octreeRuta->numCuerpos);
				Dibujante.octreePrincipal= new Octree;
				Dibujante.octreePrincipal= NULL;
			}

			Dibujante.octreePrincipal=CrearBloque(Dibujante.limites);
			if(!DesarrollarOctree(Dibujante.octreePrincipal,Dibujante.octreeRuta,Dibujante.Objetos,Dibujante.numObjetosEstablecidos,Dibujante.DXYZ,Dibujante.indiceObjetoHaptico))
			{
				MessageBox::Show("No es posible Crear jerarquia de Octree");
				DestruirBloque(Dibujante.octreePrincipal,Dibujante.octreeRuta->numCuerpos);
				Dibujante.octreePrincipal= new Octree;
				Dibujante.octreePrincipal= NULL;
			}
			else
			{
				ColisionarOctree(Dibujante.octreePrincipal,Dibujante.octreeRuta,Dibujante.Objetos,Dibujante.indiceObjetoHaptico);
				Dibujante.rehacerDibujo=true;
			}
			break;
		}

		case Keys::Multiply : // Setear Pivote ...por ahora a 0,0,0....
		{
			Dibujante.Objetos[Dibujante.indiceObjetoActivo].pivote[0]=(float)0.0;
			Dibujante.Objetos[Dibujante.indiceObjetoActivo].pivote[1]=(float)0.0;
			Dibujante.Objetos[Dibujante.indiceObjetoActivo].pivote[2]=(float)0.0;
			break;
		}

		case Keys::Divide : // Setear si se requiere del cuerpo actual
		{
			Dibujante.Objetos[Dibujante.indiceObjetoActivo].deseado=!Dibujante.Objetos[Dibujante.indiceObjetoActivo].deseado;
			actualizacion=true;
			break;
		}

		case Keys::N : // Setear si se requieren normales del cuerpo actual
		{
			Dibujante.dibNormal=!Dibujante.dibNormal;
			actualizacion=true;
			break;
		}

		default:
		{
			break;
		}
	}
};

void BigBangT::VentanaPadre::Actualizar(void)
{
	if(actListo)
	{
		actListo=false;
		Dibujante.octreeRuta->factorC=MiVentanaOctree.factorC;
		Dibujante.octreeRuta->factorU=MiVentanaOctree.factorU;
		Dibujante.octreeRuta->factorG=MiVentanaOctree.factorG;
		Dibujante.octreeRuta->factorR=MiVentanaOctree.factorR;

		register int nC=Dibujante.numObjetosEstablecidos;
		if(Dibujante.octreePrincipal!= NULL)
		{
			DestruirBloque(Dibujante.octreePrincipal,Dibujante.octreeRuta->numCuerpos);
			Dibujante.octreePrincipal= new Octree;
			for(register int i=1;i<=nC;i++)
			{
				if(Dibujante.Objetos[i].deseado && Dibujante.Objetos[i].existencia)
				{
					Dibujante.octreePrincipal=CrearBloque(Dibujante.limites);
					DesarrollarOctree(Dibujante.octreePrincipal,Dibujante.octreeRuta,Dibujante.Objetos,Dibujante.numObjetosEstablecidos,Dibujante.DXYZ,Dibujante.indiceObjetoHaptico);
					ColisionarOctree(Dibujante.octreePrincipal,Dibujante.octreeRuta,Dibujante.Objetos,Dibujante.indiceObjetoHaptico);
					i=nC+1;
				}
			}
		}
		actListo=true;
		Dibujante.rehacerDibujo=true;
	}
};

void BigBangT::VentanaPadre::MenuCOCtree_Click(System::Object^  sender, System::EventArgs^  e)
{
	MiVentanaOctree.Show();
};

void BigBangT::VentanaPadre::habilitacionH_Click(System::Object^  sender, System::EventArgs^  e)
{
	if(Dibujante.superHaptico->creacion)
	{
		Dibujante.superHaptico->habilitado=!Dibujante.superHaptico->habilitado;
		if(Dibujante.numObjetosEstablecidos>0 && Dibujante.superHaptico->habilitado)
		{
			CuerpoCopiar(&Dibujante.Objetos[0],&Dibujante.Objetos[Dibujante.indiceObjetoHaptico],true);
			Dibujante.rehacerDibujo=true; 
		}
		else if(Dibujante.numObjetosEstablecidos>0)
		{
			CuerpoCopiar(&Dibujante.Objetos[Dibujante.indiceObjetoHaptico],&Dibujante.Objetos[0],false);
			Dibujante.Objetos[0].existencia=false;
			Dibujante.superHaptico->habilitado=false;
			habilitacionH->CheckState=CheckState::Unchecked;
			Dibujante.rehacerDibujo=true; 
		}
		else
		{
			Dibujante.superHaptico->habilitado=false;
			habilitacionH->CheckState=CheckState::Unchecked;
		}
	}
	else
	{
		habilitacionH->CheckState=CheckState::Unchecked;	
	}
};

///////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void BigBangT::VentanaPadre::VentanaPadre_Load(System::Object^  sender, System::EventArgs^  e)
{
	if(miM->WaitOne())
	{
		Dibujante.Actuador.SetCurrentWindow();

		miM->ReleaseMutex();
	}
	HebraInd1->RunWorkerAsync();
};

System::Void BigBangT::VentanaPadre::HebraInd1_DoWork(System::Object^  sender, System::ComponentModel::DoWorkEventArgs^  e) 
{
	while(true)
	{
		if(miM->WaitOne())
		{
			if(volver)
			{
				if(Dibujante.Actuador.SetCurrentWindow())
				{
					volver=false;
					externo=false;
					Dibujante.Resize(w1,h1);
				}
			}
			else
			{
				if(Dibujante.superHaptico->creacion && Dibujante.superHaptico->habilitado)
				{
					Dibujante.superHaptico->Actualizar();

					if(Dibujante.indiceObjetoHapticoAnt!=Dibujante.indiceObjetoHaptico)
					{
						if(!CuerpoCopiar(&Dibujante.Objetos[Dibujante.indiceObjetoHapticoAnt],&Dibujante.Objetos[0],false))
						{
							MessageBox::Show("Error al Actualizar Cuerpo Anterior");
						}
						if(!CuerpoCopiar(&Dibujante.Objetos[0],&Dibujante.Objetos[Dibujante.indiceObjetoHaptico],true))
						{
							MessageBox::Show("Error al Actualizar Cuerpo Actual");
						}
						Dibujante.indiceObjetoHapticoAnt=Dibujante.indiceObjetoHaptico;	
					}

					if(!CuerpoActualizar(&Dibujante.Objetos[0],&Dibujante.Objetos[Dibujante.indiceObjetoHaptico],Dibujante.superHaptico->posicion,Dibujante.superHaptico->transformacion))
					{
						MessageBox::Show("Error al Actualizar Cuerpo");
					}
					actualizacion=false;
					Actualizar();
				}
				else if(actualizacion)
				{
					actualizacion=false;
					Actualizar();	
				}

				Dibujante.Renderizar(externo?Dibujante.Actuador.hdc2:Dibujante.Actuador.hdc);
			}
		}

		miM->ReleaseMutex();
	}
};

//////////////////////////////////////////////////////////////////////////////// Menu de Opciones

void BigBangT::VentanaPadre::MenuPuntos_Click(System::Object^  sender, System::EventArgs^  e)
{
	MenuLineas->CheckState=CheckState::Unchecked;
	MenuRelleno->CheckState=CheckState::Unchecked;
	Dibujante.swBackType=Dibujante.swFrontType=2;
};
void BigBangT::VentanaPadre::MenuLineas_Click(System::Object^  sender, System::EventArgs^  e)
{
	MenuPuntos->CheckState=CheckState::Unchecked;
	MenuRelleno->CheckState=CheckState::Unchecked;
	Dibujante.swBackType=Dibujante.swFrontType=1;
};
void BigBangT::VentanaPadre::MenuRelleno_Click(System::Object^  sender, System::EventArgs^  e)
{
	MenuPuntos->CheckState=CheckState::Unchecked;
	MenuLineas->CheckState=CheckState::Unchecked;
	Dibujante.swBackType=Dibujante.swFrontType=0;
};

void BigBangT::VentanaPadre::MenuSimulador_Click(System::Object^  sender, System::EventArgs^  e) 
{ 
	MenuSimulador->CheckState=CheckState::Checked;
	MenuTriangulos->CheckState=CheckState::Unchecked;
	Dibujante.rendSelec=1;
};

void BigBangT::VentanaPadre::MenuTriangulos_Click(System::Object^  sender, System::EventArgs^  e) 
{ 
	MenuSimulador->CheckState=CheckState::Unchecked;
	MenuTriangulos->CheckState=CheckState::Checked;
	Dibujante.rendSelec=2;
};


void BigBangT::VentanaPadre::colorActual_Click(System::Object^  sender, System::EventArgs^  e) 
{
	if(cD->ShowDialog()==System::Windows::Forms::DialogResult::OK)
	{
		if(Dibujante.numObjetosEstablecidos>0)
		{
			Dibujante.Objetos[Dibujante.indiceObjetoActivo].colorRGBA.Alpha((float)cD->Color.A/255.0);
			Dibujante.Objetos[Dibujante.indiceObjetoActivo].colorRGBA.Red((float)cD->Color.R/255.0);
			Dibujante.Objetos[Dibujante.indiceObjetoActivo].colorRGBA.Green((float)cD->Color.G/255.0);
			Dibujante.Objetos[Dibujante.indiceObjetoActivo].colorRGBA.Blue((float)cD->Color.B/255.0);
		}
	}
};