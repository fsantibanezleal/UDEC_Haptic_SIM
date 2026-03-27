// BigBangT.cpp : main project file.

#include "VentanaPadre.h"

using namespace BigBangT;

[STAThreadAttribute]
int main(array<System::String ^> ^args)
{
	// Enabling Windows XP visual effects before any controls are created
	Application::EnableVisualStyles();
	Application::SetCompatibleTextRenderingDefault(false); 

	// Create the main window and run it
	Application::Run(gcnew VentanaPadre());
	return 0;
}
