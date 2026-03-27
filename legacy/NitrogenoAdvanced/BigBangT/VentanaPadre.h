#pragma once

#include <windows.h>
#include <stdio.h>
#include <math.h>

#include "DibujarOpenGl.h"
#include "Cargador.h"

#include "VentanaOctree.h"
#include "VentanaHija.h"

using namespace System;
using namespace System::IO;
using namespace System::Windows::Forms;
using namespace System::Globalization;

namespace BigBangT 
{

	using namespace System;
	using namespace System::IO;
	using namespace System::Text;
	using namespace System::ComponentModel;
	using namespace System::Collections;
	using namespace System::Windows::Forms;
	using namespace System::Data;
	using namespace System::Drawing;
	using namespace System::Threading;

	/// <summary>
	/// Summary for Form1
	///
	/// WARNING: If you change the name of this class, you will need to change the
	///          'Resource File Name' property for the managed resource compiler tool
	///          associated with all .resx files this class depends on.  Otherwise,
	///          the designers will not be able to interact properly with localized
	///          resources associated with this form.
	/// </summary>

	public ref class VentanaPadre : public System::Windows::Forms::Form
	{
		private:
		public:

			VentanaHija		ventanaCentral;
			bool			actListo,actualizacion;

			VentanaOctree	MiVentanaOctree;

			Cargador		Carguero;
			DibujarOpenGl	Dibujante;
			float			dX,dY,dZ,rotX,rotY,rotZ;
			float			*factorEscala;
			int				signRotacion;
			Mutex^			miM;					

		private: System::Windows::Forms::ToolStripMenuItem^  colorActual;
		public: 
		private: System::Windows::Forms::ColorDialog^  cD;
		private: System::ComponentModel::BackgroundWorker^  HebraInd1;

		public: 
			VentanaPadre(void)
			{
				InitializeComponent();
				Inicio();
			}
		
			void Inicio(void);
			void Actualizar(void);

		protected:
			/// <summary>
			/// Clean up any resources being used.
			/// </summary>
			~VentanaPadre()
			{
				if (components)
				{
					delete components;
				}
			}


		private: System::Windows::Forms::ToolStripMenuItem^ MenuAmbiente;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuSimulador;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuTriangulos;

		private: System::Windows::Forms::ToolStripMenuItem^ habilitacionH;
		private: System::Windows::Forms::ProgressBar^		progressBar1;

		private: System::Windows::Forms::ToolStripMenuItem^ MenuCOCtree;
	
		private: System::Windows::Forms::Panel^				PanelG;
		private: System::Windows::Forms::OpenFileDialog^	AbrirFile;
		private: System::Windows::Forms::TextBox^			Memo;


		private: System::Windows::Forms::MenuStrip^			MenuPrincipal;

		private: System::Windows::Forms::ToolStripMenuItem^  inicioToolStripMenuItem;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuAbrir;

		private: System::Windows::Forms::ToolStripMenuItem^  MenuCerrar;

		private: System::Windows::Forms::ToolStripMenuItem^  MenuOpciones;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuOpenGl;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuMallado;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuPuntos;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuLineas;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuRelleno;

		private: System::Windows::Forms::ToolStripMenuItem^  MenuIluminacion;

		private: System::Windows::Forms::ToolStripMenuItem^  MenuHaptico;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuColisiones;

		private: System::Windows::Forms::ToolStripMenuItem^  objetosToolStripMenuItem;
		private: System::Windows::Forms::ToolStripMenuItem^  espacioToolStripMenuItem;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuOctree;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuVoroni;
		private: System::Windows::Forms::ToolStripMenuItem^  MenuLevel;
		private: System::ComponentModel::IContainer^		 components;

		protected: 
		private:
			/// <summary>
			/// Required designer variable.
			/// </summary>

	
		#pragma region Windows Form Designer generated code
			/// <summary>
			/// Required method for Designer support - do not modify
			/// the contents of this method with the code editor.
			/// </summary>
			void InitializeComponent(void)
			{
				this->PanelG = (gcnew System::Windows::Forms::Panel());
				this->progressBar1 = (gcnew System::Windows::Forms::ProgressBar());
				this->AbrirFile = (gcnew System::Windows::Forms::OpenFileDialog());
				this->Memo = (gcnew System::Windows::Forms::TextBox());
				this->MenuPrincipal = (gcnew System::Windows::Forms::MenuStrip());
				this->inicioToolStripMenuItem = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuAbrir = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuCerrar = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuOpciones = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuOpenGl = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuMallado = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuPuntos = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuLineas = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuRelleno = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuIluminacion = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuHaptico = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->habilitacionH = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuColisiones = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->objetosToolStripMenuItem = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->colorActual = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->espacioToolStripMenuItem = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuOctree = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuCOCtree = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuVoroni = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuLevel = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuAmbiente = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuSimulador = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->MenuTriangulos = (gcnew System::Windows::Forms::ToolStripMenuItem());
				this->cD = (gcnew System::Windows::Forms::ColorDialog());
				this->HebraInd1 = (gcnew System::ComponentModel::BackgroundWorker());
				this->PanelG->SuspendLayout();
				this->MenuPrincipal->SuspendLayout();
				this->SuspendLayout();
				// 
				// PanelG
				// 
				this->PanelG->BackColor = System::Drawing::SystemColors::ControlLight;
				this->PanelG->Controls->Add(this->progressBar1);
				this->PanelG->Location = System::Drawing::Point(228, 37);
				this->PanelG->Name = L"PanelG";
				this->PanelG->Size = System::Drawing::Size(1392, 856);
				this->PanelG->TabIndex = 0;
				this->PanelG->DoubleClick += gcnew System::EventHandler(this, &VentanaPadre::PanelG_DoubleClick);
				this->PanelG->Paint += gcnew System::Windows::Forms::PaintEventHandler(this, &VentanaPadre::PanelG_Paint);
				// 
				// progressBar1
				// 
				this->progressBar1->Location = System::Drawing::Point(550, 822);
				this->progressBar1->Name = L"progressBar1";
				this->progressBar1->Size = System::Drawing::Size(252, 23);
				this->progressBar1->TabIndex = 0;
				// 
				// AbrirFile
				// 
				this->AbrirFile->FileName = L"openFileDialog1";
				// 
				// Memo
				// 
				this->Memo->Location = System::Drawing::Point(12, 926);
				this->Memo->Multiline = true;
				this->Memo->Name = L"Memo";
				this->Memo->Size = System::Drawing::Size(124, 30);
				this->Memo->TabIndex = 1;
				this->Memo->Visible = false;
				// 
				// MenuPrincipal
				// 
				this->MenuPrincipal->Items->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(2) {this->inicioToolStripMenuItem, 
					this->MenuOpciones});
				this->MenuPrincipal->Location = System::Drawing::Point(0, 0);
				this->MenuPrincipal->Name = L"MenuPrincipal";
				this->MenuPrincipal->Size = System::Drawing::Size(1642, 24);
				this->MenuPrincipal->TabIndex = 2;
				this->MenuPrincipal->Text = L"menuStrip1";
				// 
				// inicioToolStripMenuItem
				// 
				this->inicioToolStripMenuItem->DropDownItems->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(2) {this->MenuAbrir, 
					this->MenuCerrar});
				this->inicioToolStripMenuItem->Name = L"inicioToolStripMenuItem";
				this->inicioToolStripMenuItem->Size = System::Drawing::Size(44, 20);
				this->inicioToolStripMenuItem->Text = L"Inicio";
				// 
				// MenuAbrir
				// 
				this->MenuAbrir->Name = L"MenuAbrir";
				this->MenuAbrir->Size = System::Drawing::Size(128, 22);
				this->MenuAbrir->Text = L"Abrir Obj";
				this->MenuAbrir->Click += gcnew System::EventHandler(this, &VentanaPadre::MenuAbrir_Click);
				// 
				// MenuCerrar
				// 
				this->MenuCerrar->Name = L"MenuCerrar";
				this->MenuCerrar->Size = System::Drawing::Size(128, 22);
				this->MenuCerrar->Text = L"Cerrar";
				this->MenuCerrar->Click += gcnew System::EventHandler(this, &VentanaPadre::MenuCerrar_Click);
				// 
				// MenuOpciones
				// 
				this->MenuOpciones->DropDownItems->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(4) {this->MenuOpenGl, 
					this->MenuHaptico, this->MenuColisiones, this->MenuAmbiente});
				this->MenuOpciones->Name = L"MenuOpciones";
				this->MenuOpciones->Size = System::Drawing::Size(63, 20);
				this->MenuOpciones->Text = L"Opciones";
				// 
				// MenuOpenGl
				// 
				this->MenuOpenGl->DropDownItems->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(2) {this->MenuMallado, 
					this->MenuIluminacion});
				this->MenuOpenGl->Name = L"MenuOpenGl";
				this->MenuOpenGl->Size = System::Drawing::Size(156, 22);
				this->MenuOpenGl->Text = L"OpenGl";
				// 
				// MenuMallado
				// 
				this->MenuMallado->DropDownItems->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(3) {this->MenuPuntos, 
					this->MenuLineas, this->MenuRelleno});
				this->MenuMallado->Name = L"MenuMallado";
				this->MenuMallado->Size = System::Drawing::Size(138, 22);
				this->MenuMallado->Text = L"Mallado";
				// 
				// MenuPuntos
				// 
				this->MenuPuntos->CheckOnClick = true;
				this->MenuPuntos->Name = L"MenuPuntos";
				this->MenuPuntos->Size = System::Drawing::Size(120, 22);
				this->MenuPuntos->Text = L"Puntos";
				this->MenuPuntos->Click += gcnew System::EventHandler(this, &VentanaPadre::MenuPuntos_Click);
				// 
				// MenuLineas
				// 
				this->MenuLineas->Checked = true;
				this->MenuLineas->CheckOnClick = true;
				this->MenuLineas->CheckState = System::Windows::Forms::CheckState::Checked;
				this->MenuLineas->Name = L"MenuLineas";
				this->MenuLineas->Size = System::Drawing::Size(120, 22);
				this->MenuLineas->Text = L"Lineas";
				this->MenuLineas->Click += gcnew System::EventHandler(this, &VentanaPadre::MenuLineas_Click);
				// 
				// MenuRelleno
				// 
				this->MenuRelleno->CheckOnClick = true;
				this->MenuRelleno->Name = L"MenuRelleno";
				this->MenuRelleno->Size = System::Drawing::Size(120, 22);
				this->MenuRelleno->Text = L"Relleno";
				this->MenuRelleno->Click += gcnew System::EventHandler(this, &VentanaPadre::MenuRelleno_Click);
				// 
				// MenuIluminacion
				// 
				this->MenuIluminacion->Name = L"MenuIluminacion";
				this->MenuIluminacion->Size = System::Drawing::Size(138, 22);
				this->MenuIluminacion->Text = L"Iluminacion";
				// 
				// MenuHaptico
				// 
				this->MenuHaptico->DropDownItems->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(1) {this->habilitacionH});
				this->MenuHaptico->Name = L"MenuHaptico";
				this->MenuHaptico->Size = System::Drawing::Size(156, 22);
				this->MenuHaptico->Text = L"Hapticos";
				// 
				// habilitacionH
				// 
				this->habilitacionH->CheckOnClick = true;
				this->habilitacionH->Name = L"habilitacionH";
				this->habilitacionH->Size = System::Drawing::Size(139, 22);
				this->habilitacionH->Text = L"Habilitacion";
				this->habilitacionH->Click += gcnew System::EventHandler(this, &VentanaPadre::habilitacionH_Click);
				// 
				// MenuColisiones
				// 
				this->MenuColisiones->DropDownItems->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(2) {this->objetosToolStripMenuItem, 
					this->espacioToolStripMenuItem});
				this->MenuColisiones->Name = L"MenuColisiones";
				this->MenuColisiones->Size = System::Drawing::Size(156, 22);
				this->MenuColisiones->Text = L"Sist. Colisiones";
				// 
				// objetosToolStripMenuItem
				// 
				this->objetosToolStripMenuItem->DropDownItems->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(1) {this->colorActual});
				this->objetosToolStripMenuItem->Name = L"objetosToolStripMenuItem";
				this->objetosToolStripMenuItem->Size = System::Drawing::Size(123, 22);
				this->objetosToolStripMenuItem->Text = L"Objetos";
				// 
				// colorActual
				// 
				this->colorActual->Name = L"colorActual";
				this->colorActual->Size = System::Drawing::Size(163, 22);
				this->colorActual->Text = L"Color Obj Actual";
				this->colorActual->Click += gcnew System::EventHandler(this, &VentanaPadre::colorActual_Click);
				// 
				// espacioToolStripMenuItem
				// 
				this->espacioToolStripMenuItem->DropDownItems->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(3) {this->MenuOctree, 
					this->MenuVoroni, this->MenuLevel});
				this->espacioToolStripMenuItem->Name = L"espacioToolStripMenuItem";
				this->espacioToolStripMenuItem->Size = System::Drawing::Size(123, 22);
				this->espacioToolStripMenuItem->Text = L"Espacio";
				// 
				// MenuOctree
				// 
				this->MenuOctree->DropDownItems->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(1) {this->MenuCOCtree});
				this->MenuOctree->Name = L"MenuOctree";
				this->MenuOctree->Size = System::Drawing::Size(129, 22);
				this->MenuOctree->Text = L"Octree";
				// 
				// MenuCOCtree
				// 
				this->MenuCOCtree->Name = L"MenuCOCtree";
				this->MenuCOCtree->Size = System::Drawing::Size(151, 22);
				this->MenuCOCtree->Text = L"Configuracion";
				this->MenuCOCtree->Click += gcnew System::EventHandler(this, &VentanaPadre::MenuCOCtree_Click);
				// 
				// MenuVoroni
				// 
				this->MenuVoroni->Name = L"MenuVoroni";
				this->MenuVoroni->Size = System::Drawing::Size(129, 22);
				this->MenuVoroni->Text = L"Voroni";
				// 
				// MenuLevel
				// 
				this->MenuLevel->Name = L"MenuLevel";
				this->MenuLevel->Size = System::Drawing::Size(129, 22);
				this->MenuLevel->Text = L"Level Set";
				// 
				// MenuAmbiente
				// 
				this->MenuAmbiente->DropDownItems->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(2) {this->MenuSimulador, 
					this->MenuTriangulos});
				this->MenuAmbiente->Name = L"MenuAmbiente";
				this->MenuAmbiente->Size = System::Drawing::Size(156, 22);
				this->MenuAmbiente->Text = L"Ambiente";
				// 
				// MenuSimulador
				// 
				this->MenuSimulador->Checked = true;
				this->MenuSimulador->CheckOnClick = true;
				this->MenuSimulador->CheckState = System::Windows::Forms::CheckState::Checked;
				this->MenuSimulador->Name = L"MenuSimulador";
				this->MenuSimulador->Size = System::Drawing::Size(156, 22);
				this->MenuSimulador->Text = L"Simulador";
				this->MenuSimulador->Click += gcnew System::EventHandler(this, &VentanaPadre::MenuSimulador_Click);
				// 
				// MenuTriangulos
				// 
				this->MenuTriangulos->CheckOnClick = true;
				this->MenuTriangulos->Name = L"MenuTriangulos";
				this->MenuTriangulos->Size = System::Drawing::Size(156, 22);
				this->MenuTriangulos->Text = L"Col. Triangulos";
				this->MenuTriangulos->Click += gcnew System::EventHandler(this, &VentanaPadre::MenuTriangulos_Click);
				// 
				// HebraInd1
				// 
				this->HebraInd1->DoWork += gcnew System::ComponentModel::DoWorkEventHandler(this, &VentanaPadre::HebraInd1_DoWork);
				// 
				// VentanaPadre
				// 
				this->AutoScaleDimensions = System::Drawing::SizeF(6, 13);
				this->AutoScaleMode = System::Windows::Forms::AutoScaleMode::Font;
				this->ClientSize = System::Drawing::Size(1642, 968);
				this->Controls->Add(this->Memo);
				this->Controls->Add(this->PanelG);
				this->Controls->Add(this->MenuPrincipal);
				this->MainMenuStrip = this->MenuPrincipal;
				this->Name = L"VentanaPadre";
				this->Text = L"Deteccion de Colisiones y Realimentacion Haptica de fuerzas";
				this->WindowState = System::Windows::Forms::FormWindowState::Maximized;
				this->Load += gcnew System::EventHandler(this, &VentanaPadre::VentanaPadre_Load);
				this->Paint += gcnew System::Windows::Forms::PaintEventHandler(this, &VentanaPadre::VentanaPadre_Paint);
				this->Resize += gcnew System::EventHandler(this, &VentanaPadre::VentanaPadre_Resize);
				this->KeyDown += gcnew System::Windows::Forms::KeyEventHandler(this, &VentanaPadre::VentanaPadre_KeyDown);
				this->PanelG->ResumeLayout(false);
				this->MenuPrincipal->ResumeLayout(false);
				this->MenuPrincipal->PerformLayout();
				this->ResumeLayout(false);
				this->PerformLayout();

			}
		#pragma endregion

		private: 
			System::Void VentanaPadre_Paint(System::Object^  sender, System::Windows::Forms::PaintEventArgs^  e);
			System::Void PanelG_Paint(System::Object^  sender, System::Windows::Forms::PaintEventArgs^  e); 
			System::Void MenuCerrar_Click(System::Object^  sender, System::EventArgs^  e);
			System::Void MenuAbrir_Click(System::Object^  sender, System::EventArgs^  e); 
			System::Void VentanaPadre_KeyDown(System::Object^  sender, System::Windows::Forms::KeyEventArgs^  e);
			System::Void MenuCOCtree_Click(System::Object^  sender, System::EventArgs^  e);
			System::Void VentanaPadre_Resize(System::Object^  sender, System::EventArgs^  e);
			System::Void habilitacionH_Click(System::Object^  sender, System::EventArgs^  e);
			System::Void VentanaPadre_Load(System::Object^  sender, System::EventArgs^  e);
			System::Void MenuPuntos_Click(System::Object^  sender, System::EventArgs^  e);
			System::Void MenuLineas_Click(System::Object^  sender, System::EventArgs^  e);
			System::Void MenuRelleno_Click(System::Object^  sender, System::EventArgs^  e);
			System::Void MenuSimulador_Click(System::Object^  sender, System::EventArgs^  e);
			System::Void MenuTriangulos_Click(System::Object^  sender, System::EventArgs^  e);
			System::Void colorActual_Click(System::Object^  sender, System::EventArgs^  e);
			System::Void PanelG_DoubleClick(System::Object^  sender, System::EventArgs^  e);
			System::Void HebraInd1_DoWork(System::Object^  sender, System::ComponentModel::DoWorkEventArgs^  e);
	};
}

