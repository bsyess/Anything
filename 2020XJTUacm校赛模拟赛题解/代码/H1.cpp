// Author: Yang Dong
#include<bits/stdc++.h>
using namespace std;

int a, b; // a pos, b neg
vector<int> check(int x) {
    vector<int> ret, val(x + 1);
    vector<array<int,2>> in(x + 1, {-1, -1}), out(x + 1, {-1, -1});
    int cloc = 0;
    queue<int> q;
    for(int i = 0; i <= x; ++i) {
        if(i + b <= x) out[i + b][0] = i, in[i][0] = i + b;
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
    if(cloc != x + 1) return {};
    for(int i = 1; i <= x; ++i)
        ret.push_back(val[i] - val[i - 1]);
    return ret;
}
int main() {
    cin >> a >> b;
    int l = 0, r = 1000000;
    while(l < r) {
        int mid = (l + r) >> 1;
        if(l == r - 1) mid = r;
        if(check(mid).size()) l = mid;
        else r = mid - 1;
    }
    auto z = check(l);
    printf("%d\n", l);
    for(auto g : z) printf("%d ", g);
    return 0;
}
