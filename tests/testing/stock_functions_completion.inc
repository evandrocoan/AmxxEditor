
stock bool:xs_vec_equal(const Float:vec1[], const Float:vec2[])
{
    return (vec1[0] == vec2[0]) && (vec1[1] == vec2[1]) && (vec1[2] == vec2[2]);
}

stock xs_vec_add(const Float:in1[], const Float:in2[], Float:out[])
{
    out[0] = in1[0] + in2[0];
    out[1] = in1[1] + in2[1];
    out[2] = in1[2] + in2[2];
}
