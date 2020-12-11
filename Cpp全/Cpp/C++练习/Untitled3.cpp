#include<iostream>
#include<windows.h>
using namespace std;
static int ss=50;
static int n=79;
static char a[79];
int jian();
int jia()
{
	int i=0,j=0,k=0;
	while(i<n-3)
	{
		
		Sleep(ss);
		cout<<"\r";
		
		for(j=0;j<k;j++)
		{
			cout<<" ";
		}
		cout<<a;
		for(;j<n-1;j++)
		{
			cout<<" ";
		}
		k++;
		i++;
	}
	return jian();
}
int jian()
{
	int i=0,j=0,k=n-3;
	while(i<n-1)
	{
		
		Sleep(ss);
		cout<<"\r";
		
		for(j=0;j<k;j++)
		{
			cout<<" ";
		}
		cout<<a;
		cout<<" ";
		for(;j<n;j++)
		{
			
		}
		k--;
		i++;
	}
	return jia();
}
int main()
{
	
	a[]="o_o";
	int f=strlen(a);
	n=n-f;
	jia();
	return 0;
	
}
