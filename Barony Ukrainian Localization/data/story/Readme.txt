JSON-формат для сюжетних сцен виглядає так:

{
	"version": 1,
	"press_a_to_advance": true,
	"text": [
		"*3Це рядок тексту. ",
		"Each line is simply concatenated by default.\n",
		"Insert a new line sequence with \n to add a new line anywhere.\n",
		"Use an asterisk *2 to change the size of the text box.\n",
		"The first image aka my_image1.png is used as the background to start.\n",
		"Insert an up carat aka ^ to advance to the next background image\n",
		"in the list below at any time.\n",
		"Add a hashmark aka # to pause for dramatic effect any time.\n",
		"Add multiple hashmarks for a longer pause...##### Like that.\n",
		"Each line of text should fit 80 characters. Blah blah blah blah blah blah blah.\n",
		"Історія закінчується, коли виводиться останній рядок."
	],
	"images": [
		"my_image1.png",
		"my_image2.png"
	]
}

Якщо десь пропустити кому чи інший потрібний розділовий знак, історія не завантажиться.

Розважайтеся.
