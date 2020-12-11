#include<iostream>
using namespace std;
int main()
{
	
	char ch[80];
	cout<<"enter a sentence:"<<endl;
	cin.get(ch,70,'|');
	cout<<ch<<endl;
	cin.ignore(1);
	cin.get(ch,70);
	cout<<ch<<endl;
	return 0;
	
	
	
	
	
 } 
