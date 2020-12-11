#include<iostream>
#include<cstring>
using namespace std;
int zhuanhuan(char*s,int min,int max)
{
	int n;
	n=strlen(s);
	int i,sum=0,k=1;
	for(i=max;i>=min;i--)
	{
		sum=sum+(s[i]-'0')*k;
		k=k*10;
	}
	return sum;
}
void er(int k,char*bin)
{
    int i=7;
    while(k!=1)
    {
        bin[i]=k%2+'0';
        i--;
        k=k/2;
    }
    bin[i]=k%2+'0';
}
int main()
{
	char bin[10]="00000000";
	char s[]={"125689"};
	int k=zhuanhuan(s,2,3);
	cout<<k;
	return 0;
}
