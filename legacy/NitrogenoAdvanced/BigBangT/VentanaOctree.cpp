#include "VentanaOctree.h"

void BigBangT::VentanaOctree::CBfactorC_CheckedChanged(System::Object^  sender, System::EventArgs^  e)
{
	factorC=!factorC;
};

void BigBangT::VentanaOctree::TBfactorU_Leave(System::Object^  sender, System::EventArgs^  e)
{
	factorU=int::Parse(TBfactorU->Text);
};

void BigBangT::VentanaOctree::TBfactorU_KeyDown(System::Object^  sender, System::Windows::Forms::KeyEventArgs^  e)
{
	if(e->KeyCode == Keys::Enter)
	{
		factorU=int::Parse(TBfactorU->Text);
	}
};

void BigBangT::VentanaOctree::TBfactorG_Leave(System::Object^  sender, System::EventArgs^  e)
{
	register String^ temp=TBfactorG->Text->Replace('.',',');
	factorG=float::Parse(temp);
};

void BigBangT::VentanaOctree::TBfactorG_KeyDown(System::Object^  sender, System::Windows::Forms::KeyEventArgs^  e)
{
	if(e->KeyCode == Keys::Enter)
	{ 
		register String^ temp=TBfactorG->Text->Replace('.',',');
		factorG=float::Parse(temp);
	}
};

void BigBangT::VentanaOctree::TBfactorR_Leave(System::Object^  sender, System::EventArgs^  e)
{
	register String^ temp=TBfactorR->Text->Replace('.',',');
	factorR=float::Parse(temp);
};

void BigBangT::VentanaOctree::TBfactorR_KeyDown(System::Object^  sender, System::Windows::Forms::KeyEventArgs^  e)
{
	if(e->KeyCode == Keys::Enter)
	{
		register String^ temp=TBfactorR->Text->Replace('.',',');
		factorR=float::Parse(temp);
	}
};

