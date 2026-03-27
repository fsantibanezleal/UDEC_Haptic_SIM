#include "VentanaHija.h"

extern bool volver;
System::Void BigBangT::VentanaHija::VentanaHija_KeyDown(System::Object^  sender, System::Windows::Forms::KeyEventArgs^  e) 
{
	switch (e->KeyCode )
	{
	// Salir
		case Keys::Escape : //
		{
			volver=true;
			this->Visible=false;
			break;
		}
		// Default
		default:
		{
			break;
		}
	}
};
