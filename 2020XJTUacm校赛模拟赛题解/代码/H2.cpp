// Author: Yang Dong
#include<bits/stdc++.h>
using namespace std;

int gcd(int x, int y) { return y == 0 ? x : gcd(y, x % y);}
const int MAXN = 606060;
int in[MAXN][2], out[MAXN][2], val[MAXN];
int main() {
    memset(in, -1, sizeof in);
    memset(out, -1, sizeof out);
    int a, b, ans, cloc = 0;
    cin >> a >> b;
    ans = a + b - gcd(a, b) - 1;
    queue<int> q;
    for(int i = 0; i <= ans; ++i) {
        if(i + b <= ans) out[i + b][0] = i, in[i][0] = i + b;
        if(i - a >= 0)   out[i - a][1] = i, in[i][1] = i - a;
        if(in[i][0] == -1 && in[i][1] == -1) q.push(i);
    }
    while(!q.empty()) {
        int u = q.front(), v; q.pop();
        val[u] = ++cloc;
        if(out[u][0] != -1) {
            v = out[u][0];
            in[u][0] = out[u][0] = -1;
            if(in[v][1] == -1) q.push(v);
        }
        if(out[u][1] != -1) {
            v = out[u][1];
            in[v][1] = out[u][1] = -1;
            if(in[v][0] == -1) q.push(v);
        }
    }
    printf("%d\n", ans);
    for(int i = 1; i <= ans; ++i)
        printf("%d ", val[i] - val[i - 1]);
    return 0;
}
