#pragma once

using namespace System;
using namespace System::ComponentModel;
using namespace System::Collections;
using namespace System::Windows::Forms;
using namespace System::Data;
using namespace System::Drawing;


namespace BigBangT {

	/// <summary>
	/// Summary for VentanaOctree
	///
	/// WARNING: If you change the name of this class, you will need to change the
	///          'Resource File Name' property for the managed resource compiler tool
	///          associated with all .resx files this class depends on.  Otherwise,
	///          the designers will not be able to interact properly with localized
	///          resources associated with this form.
	/// </summary>
	public ref class VentanaOctree : public System::Windows::Forms::Form
	{
		public:
			bool	factorC;
			int		factorU;
			float	factorR,factorG;
		private: System::Windows::Forms::CheckBox^  CBfactorC;
		private: System::Windows::Forms::TextBox^  TBfactorU;
		private: System::Windows::Forms::TextBox^  TBfactorG;
		private: System::Windows::Forms::TextBox^  TBfactorR;
		private: System::Windows::Forms::Label^  LfactorU;
		private: System::Windows::Forms::Label^  LfactorG;
		private: System::Windows::Forms::Label^  LfactorR;
		
		public: 
			VentanaOctree(void)
			{
				InitializeComponent();
				factorC=false;
				factorU=4;
				factorG=(float)(1.0/50.0);
				factorR=(float)0.01;
				//
				//TODO: Add the constructor code here
				//
			}

		protected:
			/// <summary>
			/// Clean up any resources being used.
			/// </summary>
			~VentanaOctree()
			{
				if (components)
				{
					delete components;
				}
			}

		private:
		/// <summary>
		/// Required designer variable.
		/// </summary>
		System::ComponentModel::Container ^components;

		#pragma region Windows Form Designer generated code
				/// <summary>
				/// Required method for Designer support - do not modify
				/// the contents of this method with the code editor.
				/// </summary>
				void InitializeComponent(void)
				{
					this->CBfactorC = (gcnew System::Windows::Forms::CheckBox());
					this->TBfactorU = (gcnew System::Windows::Forms::TextBox());
					this->TBfactorG = (gcnew System::Windows::Forms::TextBox());
					this->TBfactorR = (gcnew System::Windows::Forms::TextBox());
					this->LfactorU = (gcnew System::Windows::Forms::Label());
					this->LfactorG = (gcnew System::Windows::Forms::Label());
					this->LfactorR = (gcnew System::Windows::Forms::Label());
					this->SuspendLayout();
					// 
					// CBfactorC
					// 
					this->CBfactorC->AutoSize = true;
					this->CBfactorC->Location = System::Drawing::Point(19, 24);
					this->CBfactorC->Name = L"CBfactorC";
					this->CBfactorC->Size = System::Drawing::Size(173, 17);
					this->CBfactorC->TabIndex = 0;
					this->CBfactorC->Text = L"No desarrollar Bloque Repetido";
					this->CBfactorC->UseVisualStyleBackColor = true;
					this->CBfactorC->CheckedChanged += gcnew System::EventHandler(this, &VentanaOctree::CBfactorC_CheckedChanged);
					// 
					// TBfactorU
					// 
					this->TBfactorU->Location = System::Drawing::Point(234, 52);
					this->TBfactorU->Name = L"TBfactorU";
					this->TBfactorU->Size = System::Drawing::Size(100, 20);
					this->TBfactorU->TabIndex = 1;
					this->TBfactorU->Text = L"4";
					this->TBfactorU->TextAlign = System::Windows::Forms::HorizontalAlignment::Center;
					this->TBfactorU->KeyDown += gcnew System::Windows::Forms::KeyEventHandler(this, &VentanaOctree::TBfactorU_KeyDown);
					this->TBfactorU->Leave += gcnew System::EventHandler(this, &VentanaOctree::TBfactorU_Leave);
					// 
					// TBfactorG
					// 
					this->TBfactorG->Location = System::Drawing::Point(234, 83);
					this->TBfactorG->Name = L"TBfactorG";
					this->TBfactorG->Size = System::Drawing::Size(100, 20);
					this->TBfactorG->TabIndex = 2;
					this->TBfactorG->Text = L"0.02";
					this->TBfactorG->TextAlign = System::Windows::Forms::HorizontalAlignment::Center;
					this->TBfactorG->KeyDown += gcnew System::Windows::Forms::KeyEventHandler(this, &VentanaOctree::TBfactorG_KeyDown);
					this->TBfactorG->Leave += gcnew System::EventHandler(this, &VentanaOctree::TBfactorG_Leave);
					// 
					// TBfactorR
					// 
					this->TBfactorR->Location = System::Drawing::Point(234, 109);
					this->TBfactorR->Name = L"TBfactorR";
					this->TBfactorR->Size = System::Drawing::Size(100, 20);
					this->TBfactorR->TabIndex = 3;
					this->TBfactorR->Text = L"0.01";
					this->TBfactorR->TextAlign = System::Windows::Forms::HorizontalAlignment::Center;
					this->TBfactorR->KeyDown += gcnew System::Windows::Forms::KeyEventHandler(this, &VentanaOctree::TBfactorR_KeyDown);
					this->TBfactorR->Leave += gcnew System::EventHandler(this, &VentanaOctree::TBfactorR_Leave);
					// 
					// LfactorU
					// 
					this->LfactorU->AutoSize = true;
					this->LfactorU->Location = System::Drawing::Point(16, 52);
					this->LfactorU->Name = L"LfactorU";
					this->LfactorU->Size = System::Drawing::Size(159, 13);
					this->LfactorU->TabIndex = 4;
					this->LfactorU->Text = L"Puntos minimos para subdivision";
					// 
					// LfactorG
					// 
					this->LfactorG->AutoSize = true;
					this->LfactorG->Location = System::Drawing::Point(16, 83);
					this->LfactorG->Name = L"LfactorG";
					this->LfactorG->Size = System::Drawing::Size(197, 13);
					this->LfactorG->TabIndex = 5;
					this->LfactorG->Text = L"% de Puntos requeridos para subdivision";
					// 
					// LfactorR
					// 
					this->LfactorR->AutoSize = true;
					this->LfactorR->Location = System::Drawing::Point(16, 109);
					this->LfactorR->Name = L"LfactorR";
					this->LfactorR->Size = System::Drawing::Size(168, 13);
					this->LfactorR->TabIndex = 6;
					this->LfactorR->Text = L"% Espacio minino para subdivision";
					// 
					// VentanaOctree
					// 
					this->AutoScaleDimensions = System::Drawing::SizeF(6, 13);
					this->AutoScaleMode = System::Windows::Forms::AutoScaleMode::Font;
					this->ClientSize = System::Drawing::Size(379, 145);
					this->Controls->Add(this->LfactorR);
					this->Controls->Add(this->LfactorG);
					this->Controls->Add(this->LfactorU);
					this->Controls->Add(this->TBfactorR);
					this->Controls->Add(this->TBfactorG);
					this->Controls->Add(this->TBfactorU);
					this->Controls->Add(this->CBfactorC);
					this->FormBorderStyle = System::Windows::Forms::FormBorderStyle::Fixed3D;
					this->MaximizeBox = false;
					this->Name = L"VentanaOctree";
					this->Text = L"VentanaOctree";
					this->TopMost = true;
					this->ResumeLayout(false);
					this->PerformLayout();

				}
		#pragma endregion
		private: System::Void CBfactorC_CheckedChanged(System::Object^  sender, System::EventArgs^  e);
		private: System::Void TBfactorU_Leave(System::Object^  sender, System::EventArgs^  e);
		private: System::Void TBfactorU_KeyDown(System::Object^  sender, System::Windows::Forms::KeyEventArgs^  e);
		private: System::Void TBfactorG_Leave(System::Object^  sender, System::EventArgs^  e);
		private: System::Void TBfactorG_KeyDown(System::Object^  sender, System::Windows::Forms::KeyEventArgs^  e);
		private: System::Void TBfactorR_Leave(System::Object^  sender, System::EventArgs^  e) ;
		private: System::Void TBfactorR_KeyDown(System::Object^  sender, System::Windows::Forms::KeyEventArgs^  e);
	};
}
