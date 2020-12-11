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
void erwei(int k,char*bin)
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
void chai(char*a,int*t)
{
	char k[10];
	int i=0,j=0,m,n,min,max;
	n=strlen(a);
	while(a[i]!=0)
	{
		min=i;
		while(a[i]!='.'&&i<n)
		{
			i++;
		}
		max=i-1;
		t[j]=zhuanhuan(a,min,max);
		j++;
		i++;	
	}	
}
int he(char*a,char*er)
{
	
	char bin[10]="00000000";
	int i;
	int t[4];
	chai(a,t);
	for(i=0;i<4;i++)
	{
		if(t[i]<0||t[i]>255)
		{
			return 0;
		}
		erwei(t[i],bin);
		strcat(er,bin);
	}
	return 1;
}
int main()
{
	char a[50];
	char er[50];
	er[0]='\0';
	cin>>a;
	int b=1;
	b=he(a,er);
	if(b==0)
	{
		cout<<"data error";
	}
	else cout<<er;
	return 0;
}
